"""Ontology bridge for CurriculumShiftBench (P04).

Maps REAL platform resource categories onto a small canonical skill-category
ontology. Edges come from data (OULAD ``vle.csv`` activity types; UCI course
subjects), are versioned, and are never invented by the harness. The bridge is
the artifact under test: scenarios inject uncertainty into THIS structure, so
its edges must be verifiable from the raw snapshot.

Bridge invariants:
- every verified edge cites the dataset and the observed category value;
- unknown edges are explicit records, not silent drops;
- NOT_APPLICABLE is a first-class class distinct from any category.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

NOT_APPLICABLE = "NOT_APPLICABLE"
ABSTAIN = "ABSTAIN"

# Canonical skill/resource-category ontology (fixed, versioned; small by design
# so that mapping ambiguity is a property of the DATA, not of ontology size).
CANONICAL_CATEGORIES: tuple[str, ...] = (
    "content",        # expository material
    "assessment",     # graded or self-check activity
    "communication",  # forums, collaboration
    "reference",      # external links, glossaries, resources
    "administrative", # homepages, questionnaires, registration
)
ONTOLOGY_VERSION = "cso-p04-1.0"

# Verified OULAD activity_type -> canonical category. Every LHS value was
# observed in vle.csv of the frozen 2013-2014 snapshot (20 distinct values);
# the mapping is our annotation, so each edge carries provenance and is
# eligible for the uncertain/unknown injectors.
VERIFIED_OULAD_EDGES: dict[str, str] = {
    "oucontent": "content",
    "subpage": "content",
    "resource": "reference",
    "url": "reference",
    "glossary": "reference",
    "folder": "reference",
    "quiz": "assessment",
    "externalquiz": "assessment",
    "ouelluminate": "communication",
    "forumng": "communication",
    "oucollaborate": "communication",
    "ouwiki": "communication",
    "dualpane": "content",
    "sharedsubpage": "content",
    "page": "content",
    "htmlactivity": "content",
    "dataplus": "content",
    "homepage": "administrative",
    "questionnaire": "administrative",
    "repeatactivity": "assessment",
}

# OULAD activity types NOT covered by the verified ontology: computed at
# bridge build time from the data (see bridge_from_oulad). If the frozen
# snapshot ever gains a new activity type, it must surface here as an explicit
# unknown edge instead of silently entering the verified set.

# UCI student-performance: subject -> canonical category. Only two subjects
# exist (mathematics, portuguese); they anchor cross-subject shift.
VERIFIED_UCI_EDGES: dict[str, str] = {
    "mathematics": "content",
    "portuguese": "content",
}


@dataclass(frozen=True)
class BridgeEdge:
    source_category: str
    canonical: str
    status: str  # "verified" | "unknown" | "uncertain"
    provenance: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.status not in {"verified", "unknown", "uncertain"}:
            raise ValueError(f"invalid edge status {self.status!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0,1]")


@dataclass(frozen=True)
class OntologyBridge:
    ontology_version: str
    edges: Mapping[str, BridgeEdge]
    unknown_sources: tuple[str, ...] = field(default_factory=tuple)

    def map_source(self, source_category: str | None) -> str:
        """Map a platform category to canonical, or return NOT_APPLICABLE."""
        if source_category is None or source_category == "":
            return NOT_APPLICABLE
        edge = self.edges.get(str(source_category))
        if edge is None:
            return NOT_APPLICABLE
        return edge.canonical

    def coverage(self) -> float:
        if not self.edges:
            return 0.0
        verified = sum(1 for e in self.edges.values() if e.status == "verified")
        return verified / len(self.edges)


def bridge_from_oulad(activity_types: Mapping[str, int]) -> OntologyBridge:
    """Build the bridge from observed OULAD activity types (value = count).

    Types present in the data but absent from VERIFIED_OULAD_EDGES become
    explicit unknown edges: they are part of the benchmark, not dropped.
    """
    edges: dict[str, BridgeEdge] = {}
    unknown: list[str] = []
    for atype in sorted(activity_types):
        if atype in VERIFIED_OULAD_EDGES:
            edges[atype] = BridgeEdge(
                source_category=atype,
                canonical=VERIFIED_OULAD_EDGES[atype],
                status="verified",
                provenance=f"oulad-2013-2014:vle.csv:activity_type={atype}",
                confidence=1.0,
            )
        else:
            unknown.append(atype)
            edges[atype] = BridgeEdge(
                source_category=atype,
                canonical=NOT_APPLICABLE,
                status="unknown",
                provenance=f"oulad-2013-2014:vle.csv:activity_type={atype}:UNMAPPED",
                confidence=0.0,
            )
    return OntologyBridge(
        ontology_version=ONTOLOGY_VERSION,
        edges=edges,
        unknown_sources=tuple(unknown),
    )


def bridge_from_uci(subjects: Mapping[str, int]) -> OntologyBridge:
    edges = {
        subj: BridgeEdge(
            source_category=subj,
            canonical=VERIFIED_UCI_EDGES[subj],
            status="verified",
            provenance=f"uci-student-performance-2014:subject={subj}",
        )
        for subj in sorted(subjects)
        if subj in VERIFIED_UCI_EDGES
    }
    unknown = tuple(s for s in sorted(subjects) if s not in VERIFIED_UCI_EDGES)
    for subj in unknown:
        edges[subj] = BridgeEdge(
            source_category=subj,
            canonical=NOT_APPLICABLE,
            status="unknown",
            provenance=f"uci-student-performance-2014:subject={subj}:UNMAPPED",
            confidence=0.0,
        )
    return OntologyBridge(ontology_version=ONTOLOGY_VERSION, edges=edges, unknown_sources=unknown)
