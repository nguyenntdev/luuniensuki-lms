"""P10 data contracts: curriculum anchors, learning objects, spiral sequences.

Design paper scope (see METHOD.md in this directory). All types are frozen
dataclasses; every record is hashable via the canonical V2/V3 hash standard.

Honesty invariants enforced at construction time:
- ``CurriculumAnchor.confidence_status`` is exactly one of
  ``documented`` / ``needs_expert_review``; there is no third value that could
  launder an unverified mapping into "documented".
- ``anchor_code`` must be a non-empty identifier; the source citation is
  mandatory (no anchor without provenance).
- ``LearningObject.bloom_level`` confined to the revised Bloom range 1..6.
- ``grade`` confined to the paper's scope {10, 11, 12}.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input


class P10ContractError(ValueError):
    """Raised when a P10 record violates its schema or a design invariant."""


class UnknownAnchorError(P10ContractError):
    """Raised when an object references an anchor code absent from the registry.

    Fabrication guard: an invented competency code (e.g. a hallucinated
    official numeraire) can never silently enter a sequence. Defined here (the
    base error module) so both the registry gate and the builder gate raise
    the same typed failure without import cycles.
    """


CONFIDENCE_STATUSES = frozenset({"documented", "needs_expert_review"})
PAPER_GRADES = frozenset({10, 11, 12})
BLOOM_MIN, BLOOM_MAX = 1, 6
LAYER_NAMES = {1: "nhan_dien", 2: "doi_chieu", 3: "danh_gia"}
# Fixed Bloom bands per layer (Bruner spiral revisiting with rising depth).
LAYER_BLOOM_BANDS: dict[int, tuple[int, int]] = {1: (1, 2), 2: (3, 4), 3: (5, 5)}


@dataclass(frozen=True)
class CurriculumAnchor:
    """One claimed mapping of curriculum content to GDPT 2018 (grades 10-12).

    ``anchor_code`` identifies a curriculum element (unit / chapter / focus
    topic). ``source_citation`` names the ministerial document or the frozen
    repo-local catalog (with its SHA-256 in the registry) the mapping rests
    on. ``confidence_status`` is the honesty flag: ``documented`` only where
    the authors are certain the content is in the public Thông tư
    32/2018/TT-BGDĐT; anything requiring a teacher's judgement is
    ``needs_expert_review``.
    """

    anchor_code: str
    grade: int
    competency_ref: str
    source_citation: str
    confidence_status: str

    def __post_init__(self) -> None:
        if not self.anchor_code or not self.anchor_code.strip():
            raise P10ContractError("anchor_code is required")
        if self.grade not in PAPER_GRADES:
            raise P10ContractError(
                f"{self.anchor_code}: grade {self.grade} outside P10 scope {sorted(PAPER_GRADES)}"
            )
        if not self.competency_ref or not self.competency_ref.strip():
            raise P10ContractError(f"{self.anchor_code}: competency_ref is required")
        if not self.source_citation or not self.source_citation.strip():
            raise P10ContractError(
                f"{self.anchor_code}: source_citation is mandatory — "
                "a curriculum mapping without provenance is a fabrication"
            )
        if self.confidence_status not in CONFIDENCE_STATUSES:
            raise P10ContractError(
                f"{self.anchor_code}: confidence_status must be one of "
                f"{sorted(CONFIDENCE_STATUSES)}, got {self.confidence_status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def sha256(self) -> str:
        return sha256_input(self.to_dict())


@dataclass(frozen=True)
class LearningObject:
    """One documented heritage learning object (a Cửu Đỉnh motif)."""

    object_id: str
    urn_slug: str
    motif_name_vi: str
    category: str
    grade: int
    layer: int
    bloom_level: int
    anchor_code: str
    is_ai_generated: bool = True

    def __post_init__(self) -> None:
        if not self.object_id or not self.object_id.strip():
            raise P10ContractError("object_id is required")
        if not self.urn_slug:
            raise P10ContractError(f"{self.object_id}: urn_slug is required")
        if not self.motif_name_vi:
            raise P10ContractError(f"{self.object_id}: motif_name_vi is required")
        if not self.category:
            raise P10ContractError(f"{self.object_id}: category is required")
        if self.grade not in PAPER_GRADES:
            raise P10ContractError(
                f"{self.object_id}: grade {self.grade} outside {sorted(PAPER_GRADES)}"
            )
        if self.layer not in LAYER_NAMES:
            raise P10ContractError(
                f"{self.object_id}: layer must be 1|2|3, got {self.layer!r}"
            )
        if not (BLOOM_MIN <= self.bloom_level <= BLOOM_MAX):
            raise P10ContractError(
                f"{self.object_id}: bloom_level {self.bloom_level} outside {BLOOM_MIN}..{BLOOM_MAX}"
            )
        lo, hi = LAYER_BLOOM_BANDS[self.layer]
        if not (lo <= self.bloom_level <= hi):
            raise P10ContractError(
                f"{self.object_id}: bloom_level {self.bloom_level} outside layer-{self.layer} "
                f"band {lo}..{hi} (Bruner depth contract)"
            )
        if not self.anchor_code:
            raise P10ContractError(
                f"{self.object_id}: anchor_code is required — an unanchored object "
                "cannot enter a curriculum-gated sequence"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def sha256(self) -> str:
        return sha256_input(self.to_dict())


@dataclass(frozen=True)
class PrerequisiteEdge:
    """Directed edge u -> v: u is a prerequisite of v."""

    tail: str  # u
    head: str  # v
    edge_kind: str = "progression"  # progression | bridge

    def __post_init__(self) -> None:
        if self.tail == self.head:
            raise P10ContractError(f"self-loop at {self.tail!r} is never a valid prerequisite")
        if self.edge_kind not in {"progression", "bridge"}:
            raise P10ContractError(
                f"edge_kind must be 'progression' or 'bridge', got {self.edge_kind!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SequenceCertificate:
    """Machine-checkable outcome of the four design invariants for one order."""

    acyclic: bool
    grade_monotone: bool
    bloom_ascent_ok: bool
    anchors_resolved: bool
    bloom_leap_edges: tuple[str, ...]  # edges whose jump exceeds max_leap (flag, not reject)
    reason_codes: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return (
            self.acyclic
            and self.grade_monotone
            and self.bloom_ascent_ok
            and self.anchors_resolved
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "acyclic": self.acyclic,
            "grade_monotone": self.grade_monotone,
            "bloom_ascent_ok": self.bloom_ascent_ok,
            "anchors_resolved": self.anchors_resolved,
            "valid": self.valid,
            "bloom_leap_edges": list(self.bloom_leap_edges),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class SpiralSequence:
    """An ordered design over learning objects with its invariant certificate."""

    design_id: str  # C0 | C1 | proposed | A1..A4
    ordered_object_ids: tuple[str, ...]
    certificate: SequenceCertificate
    needs_expert_review_anchor_count: int
    documented_anchor_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_id": self.design_id,
            "ordered_object_ids": list(self.ordered_object_ids),
            "certificate": self.certificate.to_dict(),
            "documented_anchor_count": self.documented_anchor_count,
            "needs_expert_review_anchor_count": self.needs_expert_review_anchor_count,
        }

    def sha256(self) -> str:
        return sha256_input(self.to_dict())
