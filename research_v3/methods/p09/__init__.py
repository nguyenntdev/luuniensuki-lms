"""P09 — Provenance-Aware Interactive Cultural Heritage Exploration.

Method package for Research V3 paper P09. Deterministic provenance model,
fail-closed verification gate, and gated exploration policy. See METHOD.md.
"""
from __future__ import annotations

from .provenance import (
    ABSTAIN_LABEL,
    DECISIONS,
    EPISTEMIC_STATUSES,
    LOCATOR_KINDS,
    METHOD_ID,
    METHOD_VERSION,
    PAPER_ID,
    REJECT_LABEL,
    SOURCE_KINDS,
    SURFACE_LABEL,
    Claim,
    Locator,
    ProvenanceCorpus,
    ProvenanceError,
    SourceRef,
    SurfaceDecision,
    VerificationResult,
    verify_claim,
)
from .policy import DEFAULTS, propose_surface
from .baselines import C0_METHOD_ID, C1_METHOD_ID, c0_surface_everything, c1_keyword_match
from .metrics import (
    EVAL_VERSION,
    abstention_rate,
    audit_sample,
    citation_grounding_rate,
    evaluate_method,
    unsupported_surfacing_rate,
    write_audit_sample,
)

__all__ = [
    "ABSTAIN_LABEL",
    "C0_METHOD_ID",
    "C1_METHOD_ID",
    "DECISIONS",
    "DEFAULTS",
    "EPISTEMIC_STATUSES",
    "EVAL_VERSION",
    "LOCATOR_KINDS",
    "METHOD_ID",
    "METHOD_VERSION",
    "PAPER_ID",
    "REJECT_LABEL",
    "SOURCE_KINDS",
    "SURFACE_LABEL",
    "Claim",
    "Locator",
    "ProvenanceCorpus",
    "ProvenanceError",
    "SourceRef",
    "SurfaceDecision",
    "VerificationResult",
    "abstention_rate",
    "audit_sample",
    "c0_surface_everything",
    "c1_keyword_match",
    "citation_grounding_rate",
    "evaluate_method",
    "propose_surface",
    "unsupported_surfacing_rate",
    "verify_claim",
    "write_audit_sample",
]
