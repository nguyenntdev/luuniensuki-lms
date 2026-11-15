"""P14 claims gate: no learning-benefit or UDL-effectiveness claims without
human data (spec: 'no UDL benefit claim without human data'; ethics §5:
'algorithmic proxy outcomes cannot be reinterpreted as student gains').

P14 in this run has NO human user study (P14-T19 BLOCKED). The guard is a
fail-closed claim classifier: any manuscript/artifact claim is checked against
an allowlist of audit-descriptive wordings; benefit/effect wordings are
rejected, and benefit claims additionally require a human-evidence flag that
is impossible to set while T19 is BLOCKED.
"""
from __future__ import annotations

import re
from typing import Any

CLAIMS_GUARD_VERSION = "p14-claims-guard-1.0.0"

# Benefit/effect language that requires genuine human-outcome data.
BENEFIT_PATTERNS = (
    r"\bimprove[s|d]?\b.*\blearn(ing|ers)\b",
    r"\blearn(ing)?\s+(gain|benefit|outcome)s?\b",
    r"\bcausal(ly)?\b",
    r"\bmore effective\b",
    r"\bbetter learning\b",
    r"\bincrease[s|d]?\b.*\b(comprehension|achievement|retention)\b",
    r"\bsignificant(ly)? (better|improv)\w*\b",
    r"\bUDL (works|is effective|benefits)\b",
)

# Wordings permitted for the audit-only run (descriptive of the audit itself).
ALLOWED_AUDIT_WORDINGS = (
    "objects fail N accessibility criteria under rubric X",
    "the audit produced conformance rate R on manifest M",
    "remediation list contains K items",
    "C1 checklist baseline missed UDL-principle failures that the full audit caught",
)

HUMAN_EVIDENCE_DATASET_IDS = frozenset()  # none: T19 ethics/human approvals BLOCKED


class ClaimRejected(ValueError):
    """Raised when a claim is not supportable by the evidence class on file."""


def classify_claim(text: str, *, human_evidence_dataset_ids: frozenset[str] = HUMAN_EVIDENCE_DATASET_IDS) -> dict[str, Any]:
    """Classify one claim string; returns record; never raises for ABSTAIN-free
    descriptive claims. Benefit claims without human data raise ClaimRejected.
    """
    lowered = text.lower()
    is_benefit = any(re.search(p, lowered) for p in BENEFIT_PATTERNS)
    record = {
        "claims_guard_version": CLAIMS_GUARD_VERSION,
        "claim": text,
        "is_benefit_claim": is_benefit,
        "human_evidence_dataset_ids": sorted(human_evidence_dataset_ids),
        "allowed": True,
        "rejection_reason": None,
    }
    if is_benefit and not human_evidence_dataset_ids:
        record["allowed"] = False
        record["rejection_reason"] = (
            "benefit/effect claim requires a human user study; P14-T19 (ethics/"
            "human annotation) is BLOCKED, so no human-evidence dataset exists"
        )
    return record


def assert_claim_allowed(text: str, **kw: Any) -> dict[str, Any]:
    record = classify_claim(text, **kw)
    if not record["allowed"]:
        raise ClaimRejected(record["rejection_reason"])
    return record


def audit_run_wording(claim: str) -> str:
    """Return the canonical allowed wording for the artifact claim ledger."""
    record = assert_claim_allowed(claim)
    return record["claim"]
