"""P12 baselines: C0 (no-citation pass-through) and C1 (citation-presence).

Both arms consume the *same* claim records as the proposed ledger arm; they
differ only in validation strictness (METHOD §4). No tuning, no extra inputs.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v3.methods.p12.ledger import ClaimEntry, SourceRecord

__all__ = ["baseline_c0", "baseline_c1"]


def baseline_c0(claims: Iterable[ClaimEntry]) -> dict[str, Any]:
    """C0 — no-citation pass-through: every claim accepted as-is.

    Sanity floor (SCIENTIFIC_EVALUATION §3). Detects nothing by construction.
    """
    claim_list = list(claims)
    n = len(claim_list)
    return {
        "baseline": "C0",
        "name": "no-citation pass-through",
        "n_claims": n,
        "accepted": n,
        "rejected": [],
        "unsourced_claim_rate": 0.0,  # pass-through never rejects => reports zero defects
        "locator_completeness_rate": 0.0,
        "contradiction_count": 0,
        "verdict_counts": {"PASS": n, "REJECT": 0, "ABSTAIN": 0},
        "note": "Sanity floor: zero scrutiny, zero detected defects. Never a serious comparator.",
    }


def baseline_c1(
    claims: Iterable[ClaimEntry],
    registry: Mapping[str, SourceRecord] | None = None,
) -> dict[str, Any]:
    """C1 — citation-presence check ("thư mục thông thường"): PASS iff any
    non-empty citation string exists (source_id or locator fields). No source
    resolution, no locator schema, no stance semantics, no chain."""
    registry = registry or {}
    verdicts: list[dict[str, Any]] = []
    for c in claims:
        has_any = bool(c.source_id) or c.locator is not None
        verdicts.append({"claim_id": c.claim_id, "verdict": "PASS" if has_any else "REJECT"})

    n = len(verdicts)
    n_reject = sum(1 for v in verdicts if v["verdict"] == "REJECT")
    # C1 cannot distinguish unknown sources or missing locators once *some*
    # citation-ish string exists — that blindness is the comparator's point.
    return {
        "baseline": "C1",
        "name": "citation-presence check",
        "n_claims": n,
        "accepted": n - n_reject,
        "rejected": [v["claim_id"] for v in verdicts if v["verdict"] == "REJECT"],
        "unsourced_claim_rate": (n_reject / n) if n else None,
        "locator_completeness_rate": None,  # not measurable under C1 semantics
        "contradiction_count": 0,  # C1 has no stance semantics
        "verdict_counts": {"PASS": n - n_reject, "REJECT": n_reject, "ABSTAIN": 0},
        "note": "Presence-only: an unresolvable source_id with a locator still passes.",
    }
