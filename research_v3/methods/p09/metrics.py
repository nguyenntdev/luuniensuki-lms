"""P09 metrics: citation grounding, unsupported surfacing, abstention, audit sample.

Computed from (frozen claims + sidecar verification outcomes + method decisions).
The verification sidecar is never an input to any policy; it is only the
scoring reference. All functions are pure and deterministic.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from research_v3.eval.statistics import proportion_ci

from .provenance import SURFACE_LABEL

EVAL_VERSION = "p09-eval-v1.0.0"


def unsupported_surfacing_rate(decisions: Sequence[Mapping[str, Any]], outcomes: Mapping[str, str]) -> float:
    """Primary metric: surfaced claims whose verification outcome is not 'verified'."""
    surfaced = [d for d in decisions if d["decision"] == SURFACE_LABEL]
    if not surfaced:
        return 0.0
    bad = [d for d in surfaced if outcomes.get(d["claim_id"]) != "verified"]
    return len(bad) / len(decisions)


def citation_grounding_rate(decisions: Sequence[Mapping[str, Any]], outcomes: Mapping[str, str]) -> float:
    """Fraction of ALL claims that are surfaced AND carry a verified-grounding citation."""
    if not decisions:
        return 0.0
    grounded = [
        d
        for d in decisions
        if d["decision"] == SURFACE_LABEL
        and outcomes.get(d["claim_id"]) == "verified"
        and d.get("evidence_ids")
    ]
    return len(grounded) / len(decisions)


def abstention_rate(decisions: Sequence[Mapping[str, Any]]) -> float:
    if not decisions:
        return 0.0
    return sum(1 for d in decisions if d["decision"] == "abstain_unverified") / len(decisions)


def evaluate_method(
    method_id: str,
    decisions: Sequence[Mapping[str, Any]],
    outcomes: Mapping[str, str],
) -> dict[str, Any]:
    """Full metric block for one method over the frozen corpus."""
    n = len(decisions)
    surfaced = [d for d in decisions if d["decision"] == SURFACE_LABEL]
    unsupported = [d for d in surfaced if outcomes.get(d["claim_id"]) != "verified"]
    grounded = [
        d
        for d in decisions
        if d["decision"] == SURFACE_LABEL and outcomes.get(d["claim_id"]) == "verified"
    ]
    abstained = [d for d in decisions if d["decision"] == "abstain_unverified"]
    rejected = [d for d in decisions if d["decision"] == "reject_invalid_source"]
    report: dict[str, Any] = {
        "method_id": method_id,
        "n_claims": n,
        "n_surfaced": len(surfaced),
        "n_grounded_surfaced": len(grounded),
        "n_unsupported_surfaced": len(unsupported),
        "citation_grounding_rate": citation_grounding_rate(decisions, outcomes),
        "unsupported_claim_surfacing_rate": unsupported_surfacing_rate(decisions, outcomes),
        "abstention_rate": abstention_rate(decisions),
        "n_rejected_invalid": len(rejected),
    }
    if unsupported:
        report["unsupported_ci95"] = proportion_ci(len(unsupported), n)
    else:
        # Zero-error case must never report [0, 0]; Clopper-Pearson upper bound.
        report["unsupported_ci95"] = proportion_ci(0, n)
    return report


def audit_sample(
    claims: Sequence[Mapping[str, Any]],
    decisions_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    seed: int = 42,
    fraction: float = 0.2,
    min_n: int = 8,
) -> list[dict[str, Any]]:
    """Deterministic human-audit sample: claims + each method's decision + provenance.

    The list is produced for an INDEPENDENT human auditor. This pipeline does
    not label it and must never claim expert verification of these items.
    """
    rng = random.Random(seed)
    ids = [c["claim_id"] for c in claims]
    n = max(min_n, int(round(fraction * len(ids))))
    n = min(n, len(ids))
    sampled = sorted(rng.sample(ids, n))
    dec_by_id: dict[str, dict[str, Mapping[str, Any]]] = {}
    for method_id, decisions in decisions_by_method.items():
        for d in decisions:
            dec_by_id.setdefault(d["claim_id"], {})[method_id] = d
    claim_by_id = {c["claim_id"]: c for c in claims}
    rows: list[dict[str, Any]] = []
    for cid in sampled:
        claim = claim_by_id[cid]
        rows.append(
            {
                "claim_id": cid,
                "claim_text": claim["text"],
                "entity_qid": claim["entity_qid"],
                "declared_source_id": claim["source"]["source_id"],
                "declared_locator": claim["locator"],
                "audit_task": (
                    "1) Confirm/deny the locator resolves inside the cited source. "
                    "2) Confirm/deny the claim text is a fair reading of that locator. "
                    "3) Mark any claim whose citation does not support it."
                ),
                "decisions": {
                    mid: dict(dec_by_id[cid][mid]) for mid in sorted(decisions_by_method)
                }
                if cid in dec_by_id
                else {},
                "auditor_fields": {"locator_resolves": None, "fair_reading": None, "notes": None},
            }
        )
    return rows


def write_audit_sample(rows: Sequence[Mapping[str, Any]], path: Path) -> str:
    """Write the audit sample and return its sha256 (for the manifest)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"audit_version": EVAL_VERSION, "auditor_instructions": (
        "You are an independent human auditor. For each claim, open the cited "
        "source URL, check the locator, and fill auditor_fields. Do NOT assume "
        "the pipeline's badge is correct; the pipeline does not produce expert labels."
    ), "sample": list(rows)}
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
