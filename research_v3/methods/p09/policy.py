"""P09 exploration policy: provenance-gated surfacing with explicit abstention.

Decision table (fail-closed; see METHOD.md §5):
  gate verified   -> surface (with source + locator + visible epistemic badge)
  gate unverified -> abstain_unverified (visible placeholder, no claim text)
  gate invalid    -> reject_invalid_source (structural citation failure)
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v3.contracts.cards import ContractError

from .provenance import (
    ABSTAIN_LABEL,
    BADGE_SURFACE_REASON,
    Claim,
    PAPER_ID,
    REJECT_LABEL,
    SURFACE_LABEL,
    METHOD_ID,
    METHOD_VERSION,
    ProvenanceCorpus,
    SurfaceDecision,
    VerificationResult,
    verify_claim,
)

DEFAULTS: Mapping[str, Any] = {
    "provenance_gate": True,
    "visible_epistemic_badge": True,
}


def propose_surface(
    claim: Claim, corpus: ProvenanceCorpus, config: Mapping[str, Any] | None = None
) -> SurfaceDecision:
    """Map one claim to a surface/abstain/reject decision (pure, deterministic)."""
    cfg = dict(DEFAULTS)
    if config:
        cfg.update({k: v for k, v in config.items() if k in DEFAULTS})
    result: VerificationResult = verify_claim(claim, corpus)
    if not cfg["provenance_gate"]:
        raise ContractError(
            "P09 proposed policy requires the provenance gate; disable-gate "
            "behaviour lives in ablations, never in the proposed method"
        )
    if result.outcome == "verified":
        badge = "verified" if cfg["visible_epistemic_badge"] else "verified"
        return SurfaceDecision(
            claim_id=claim.claim_id,
            method_id=METHOD_ID,
            method_version=METHOD_VERSION,
            decision=SURFACE_LABEL,
            epistemic_badge=badge,
            reason_codes=("gate_verified",) + ((BADGE_SURFACE_REASON,) if cfg["visible_epistemic_badge"] else ()),
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
    if result.outcome == "unverified":
        return SurfaceDecision(
            claim_id=claim.claim_id,
            method_id=METHOD_ID,
            method_version=METHOD_VERSION,
            decision=ABSTAIN_LABEL,
            epistemic_badge="unverified",
            reason_codes=("fail_closed_gate",) + result.reason_codes,
            evidence_ids=(),
        )
    return SurfaceDecision(
        claim_id=claim.claim_id,
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        decision=REJECT_LABEL,
        epistemic_badge=claim.epistemic,
        reason_codes=("fail_closed_gate",) + result.reason_codes,
        evidence_ids=(),
    )
