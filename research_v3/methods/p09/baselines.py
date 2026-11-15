"""P09 baselines: C0 "surface everything" and C1 "keyword match on claim text".

Scientific labeling: both are deterministic heuristic baselines run only as
sanity/matched-classical comparators on the frozen offline corpus. C1's keyword
vocabulary is a fixed heritage-term list, NOT a learned model and NOT a real
user-facing system.
"""
from __future__ import annotations

from typing import Any, Mapping

from .provenance import (
    Claim,
    METHOD_ID,
    METHOD_VERSION,
    PAPER_ID,
    ProvenanceCorpus,
    SurfaceDecision,
)

C0_METHOD_ID = "c0_surface_everything"
C0_METHOD_VERSION = "p09-c0-v1.0.0"
C1_METHOD_ID = "c1_keyword_match"
C1_METHOD_VERSION = "p09-c1-v1.0.0"


HERITAGE_KEYWORDS: tuple[str, ...] = (
    "citadel",
    "tomb",
    "temple",
    "palace",
    "gate",
    "fortress",
    "mausoleum",
    "shrine",
    "esplanade",
    "imperial",
    "emperor",
    "dynasty",
    "unesco",
    "heritage",
    "monument",
    "built",
    "constructed",
    "located",
    "coordinates",
    "part of",
)


def _base(claim: Claim, method_id: str, method_version: str) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id,
        "method_id": method_id,
        "method_version": method_version,
    }


def c0_surface_everything(
    claim: Claim, corpus: ProvenanceCorpus, config: Mapping[str, Any] | None = None
) -> SurfaceDecision:
    """C0: surface every claim, badge it 'verified', regardless of gate outcome.

    This baseline embodies the no-provenance status quo; its unsupported-claim
    surfacing rate equals the corpus unverified+invalid rate by construction.
    """
    return SurfaceDecision(
        claim_id=claim.claim_id,
        method_id=C0_METHOD_ID,
        method_version=C0_METHOD_VERSION,
        decision="surface",
        epistemic_badge="verified",
        reason_codes=("c0_no_gate",),
        evidence_ids=(claim.source.source_id,),
        citation={
            "source_id": claim.source.source_id,
            "source_url": claim.source.url,
            "source_sha256": claim.source.sha256,
            "locator_kind": claim.locator.kind,
            "locator_value": claim.locator.value,
            "license": claim.source.license,
        },
    )


def c1_keyword_match(
    claim: Claim, corpus: ProvenanceCorpus, config: Mapping[str, Any] | None = None
) -> SurfaceDecision:
    """C1: surface iff claim text contains a heritage keyword; NO provenance check.

    Deterministic heuristic proxy for "filter by text, not by source". It can
    surface unsupported claims (keyword present, source invalid) and abstain on
    supported ones (keyword absent) — that is the failure family under study.
    """
    text = claim.text.lower()
    if any(keyword in text for keyword in HERITAGE_KEYWORDS):
        return SurfaceDecision(
            claim_id=claim.claim_id,
            method_id=C1_METHOD_ID,
            method_version=C1_METHOD_VERSION,
            decision="surface",
            epistemic_badge="verified",
            reason_codes=("c1_keyword_hit",),
            evidence_ids=(claim.source.source_id,),
            citation={
                "source_id": claim.source.source_id,
                "source_url": claim.source.url,
                "source_sha256": claim.source.sha256,
                "locator_kind": claim.locator.kind,
                "locator_value": claim.locator.value,
                "license": claim.source.license,
            },
        )
    return SurfaceDecision(
        claim_id=claim.claim_id,
        method_id=C1_METHOD_ID,
        method_version=C1_METHOD_VERSION,
        decision="abstain_unverified",
        epistemic_badge="unverified",
        reason_codes=("c1_keyword_miss",),
        evidence_ids=(),
    )
