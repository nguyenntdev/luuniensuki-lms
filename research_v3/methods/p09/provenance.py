"""P09 provenance model: claim -> source -> locator with fail-closed verification.

Dataclasses and the verification gate for provenance-aware heritage exploration.
Every surfaced claim must carry a verifiable citation; unverified claims are
withheld with an explicit abstention (never silently dropped). See METHOD.md in
this package for the frozen invariants (I1-I4).

Scientific labeling: deterministic rule system, no learned parameters, no LLM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Mapping

METHOD_ID = "proposed"
METHOD_VERSION = "p09-provenance-v1.0.0"
PAPER_ID = "P09"

SOURCE_KINDS = frozenset(
    {"wikidata_entity", "wikidata_statement", "archive_document", "published_work"}
)
LOCATOR_KINDS = frozenset({"statement_guid", "property", "section", "page"})
EPISTEMIC_STATUSES = frozenset({"verified", "unverified", "disputed"})
VERIFICATION_OUTCOMES = frozenset({"verified", "unverified", "invalid"})
DECISIONS = frozenset({"surface", "abstain_unverified", "reject_invalid_source"})

STATEMENT_GUID_RE = re.compile(
    r"^(Q\d+)\$[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
PROPERTY_RE = re.compile(r"^P\d+$")
QID_RE = re.compile(r"^Q\d+$")

ABSTAIN_LABEL = "abstain_unverified"
REJECT_LABEL = "reject_invalid_source"
SURFACE_LABEL = "surface"

BADGE_SURFACE_REASON = "epistemic_badge_visible"


class ProvenanceError(ValueError):
    """Raised when a provenance record violates the frozen contract."""


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(f"{name} must be a non-empty string")
    return value


def _require_text_or_empty(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ProvenanceError(f"{name} must be a string")
    return value


@dataclass(frozen=True)
class SourceRef:
    """One citable source; sha256 records the raw response bytes when fetched."""

    source_id: str
    kind: str
    title: str
    url: str
    license: str
    retrieved_at: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        _require_text(self.title, "title")
        _require_text(self.url, "url")
        # license is validated as a string but MAY be empty: an empty/missing
        # rights statement is a data condition under study (spec §5 stress
        # stratum), so the gate must see it, not the constructor.
        _require_text_or_empty(self.license, "license")
        _require_text(self.retrieved_at, "retrieved_at")
        if self.kind not in SOURCE_KINDS:
            raise ProvenanceError(f"invalid source kind {self.kind!r}")
        if self.sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ProvenanceError(f"sha256 must be 64 lowercase hex chars, got {self.sha256!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Locator:
    """Where inside a source a claim lives."""

    source_id: str
    kind: str
    value: str

    def __post_init__(self) -> None:
        _require_text(self.source_id, "locator.source_id")
        _require_text(self.value, "locator.value")
        if self.kind not in LOCATOR_KINDS:
            raise ProvenanceError(f"invalid locator kind {self.kind!r}")
        # Kind-specific structural checks that are checkable WITHOUT a source:
        # statement-guid shape, property shape, page positivity, section text.
        # (The guid-QID prefix match needs the real source and is enforced by
        # the gate in verify_claim.)
        if self.kind == "statement_guid" and not STATEMENT_GUID_RE.fullmatch(self.value):
            raise ProvenanceError(f"malformed statement_guid locator {self.value!r}")
        if self.kind == "property" and not PROPERTY_RE.fullmatch(self.value):
            raise ProvenanceError(f"malformed property locator {self.value!r}")
        if self.kind == "page":
            try:
                if int(self.value) <= 0:
                    raise ProvenanceError(f"nonpositive page locator {self.value!r}")
            except ValueError as exc:
                raise ProvenanceError(f"malformed page locator {self.value!r}") from exc
        if self.kind == "section" and not self.value.strip():
            raise ProvenanceError("empty section locator")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    """One candidate claim with declared epistemic badge (default: unverified)."""

    claim_id: str
    entity_qid: str
    text: str
    source: SourceRef
    locator: Locator
    epistemic: str = "unverified"
    property_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.text, "text")
        if not QID_RE.fullmatch(self.entity_qid):
            raise ProvenanceError(f"entity_qid must look like Q<number>, got {self.entity_qid!r}")
        if self.epistemic not in EPISTEMIC_STATUSES:
            raise ProvenanceError(f"invalid epistemic badge {self.epistemic!r}")
        if self.property_id is not None and not PROPERTY_RE.fullmatch(self.property_id):
            raise ProvenanceError(f"property_id must look like P<number>, got {self.property_id!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationResult:
    """Gate decision for one claim; outcome is distinct from the declared badge."""

    claim_id: str
    outcome: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.outcome not in VERIFICATION_OUTCOMES:
            raise ProvenanceError(f"invalid verification outcome {self.outcome!r}")

    def to_dict(self) -> dict[str, Any]:
        return {"claim_id": self.claim_id, "outcome": self.outcome, "reason_codes": list(self.reason_codes)}


@dataclass(frozen=True)
class SurfaceDecision:
    """Policy output: surface with provenance bundle, or explicit abstain/reject."""

    claim_id: str
    method_id: str
    method_version: str
    decision: str
    epistemic_badge: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    citation: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ProvenanceError(f"invalid surface decision {self.decision!r}")
        if self.decision == SURFACE_LABEL and self.epistemic_badge != "verified":
            raise ProvenanceError("surface decisions must carry a verified badge")
        if self.decision != SURFACE_LABEL and self.citation is not None:
            raise ProvenanceError("abstain/reject decisions must not carry a citation")
        if self.decision == SURFACE_LABEL and not self.evidence_ids:
            raise ProvenanceError("surface decisions must cite at least one source id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "method_id": self.method_id,
            "method_version": self.method_version,
            "decision": self.decision,
            "epistemic_badge": self.epistemic_badge,
            "reason_codes": list(self.reason_codes),
            "evidence_ids": list(self.evidence_ids),
            "citation": dict(self.citation) if self.citation is not None else None,
        }


@dataclass
class ProvenanceCorpus:
    """Frozen source registry + statement index built from real snapshots."""

    sources: dict[str, SourceRef] = field(default_factory=dict)
    statement_index: dict[str, frozenset[str]] = field(default_factory=dict)

    def add_source(self, source: SourceRef, statement_guids: frozenset[str] | None = None) -> None:
        if source.source_id in self.sources:
            raise ProvenanceError(f"duplicate source id {source.source_id!r}")
        self.sources[source.source_id] = source
        if statement_guids is not None:
            self.statement_index[source.source_id] = statement_guids

    def has_source(self, source_id: str) -> bool:
        return source_id in self.sources

    def statement_guids(self, source_id: str) -> frozenset[str] | None:
        return self.statement_index.get(source_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sources": {k: v.to_dict() for k, v in sorted(self.sources.items())},
            "statement_counts": {k: len(v) for k, v in sorted(self.statement_index.items())},
        }


def validate_locator_structure(locator: Locator, source: SourceRef) -> tuple[bool, tuple[str, ...]]:
    """Structural locator validation (I1). Returns (ok, reason_codes)."""
    reasons: list[str] = []
    if locator.source_id != source.source_id:
        reasons.append("locator_source_mismatch")
    if locator.kind == "statement_guid":
        match = STATEMENT_GUID_RE.fullmatch(locator.value)
        if not match:
            reasons.append("malformed_statement_guid")
        elif match.group(1) != _qid_of_source(source):
            reasons.append("guid_qid_mismatch")
    elif locator.kind == "property":
        if not PROPERTY_RE.fullmatch(locator.value):
            reasons.append("malformed_property_locator")
    elif locator.kind == "page":
        try:
            if int(locator.value) <= 0:
                reasons.append("nonpositive_page")
        except ValueError:
            reasons.append("malformed_page_locator")
    elif locator.kind == "section" and not locator.value.strip():
        reasons.append("empty_section")
    return (not reasons, tuple(reasons))


def _qid_of_source(source: SourceRef) -> str | None:
    if source.kind in ("wikidata_entity", "wikidata_statement"):
        match = QID_RE.match(source.source_id.split("/")[-1])
        return match.group(0) if match else None
    return None


def verify_claim(claim: Claim, corpus: ProvenanceCorpus) -> VerificationResult:
    """Fail-closed verification gate. Never upgrades a claim (invariant I4)."""
    source = corpus.sources.get(claim.locator.source_id)
    if source is None:
        return VerificationResult(
            claim.claim_id, "invalid", ("nonexistent_source_id",)
        )
    # The claim's declared source must be the locator's source as well (I1).
    if claim.source.source_id != claim.locator.source_id:
        return VerificationResult(
            claim.claim_id, "invalid", ("claim_source_locator_mismatch",)
        )
    # The claim's declared source must faithfully match the registry snapshot
    # (rights/license/sha tampering detection). A divergence means the citation
    # as presented is not the citation as registered: fail closed.
    if claim.source.to_dict() != source.to_dict():
        return VerificationResult(
            claim.claim_id, "invalid", ("source_registry_mismatch",)
        )
    ok, reasons = validate_locator_structure(claim.locator, source)
    if not ok:
        return VerificationResult(claim.claim_id, "invalid", ("invalid_locator",) + reasons)
    if not source.license.strip():
        # Missing rights statement: a source without a usable license must never
        # back a surfaced claim (spec §5 "missing rights statement" stratum).
        return VerificationResult(claim.claim_id, "invalid", ("missing_rights_statement",))
    guids = corpus.statement_guids(source.source_id)
    if claim.locator.kind == "statement_guid" and guids is not None:
        if claim.locator.value not in guids:
            return VerificationResult(claim.claim_id, "invalid", ("unresolvable_statement_guid",))
    if claim.epistemic == "verified":
        return VerificationResult(claim.claim_id, "verified", ("gate_passed",))
    return VerificationResult(
        claim.claim_id, "unverified", ("badge_not_verified", claim.epistemic)
    )
