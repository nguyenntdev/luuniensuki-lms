"""LN-05 study metrics.

Primary endpoint (LN-05-17): security-utility frontier — false award rate
(FAR) versus legitimate award recall under threat models. A policy cannot win
by driving false accepts to zero while destroying legitimate award utility;
both sides of the frontier are always reported together.

Additional study metrics:
- ``duplicate_grant_count``: number of grants awarded for content-identical
  submissions sharing one dedup key beyond the first (must be 0 for I1).
- ``replay_containment``: fraction of replay deliveries correctly labelled.
- Accuracy / confusion over the frozen V2 label space.

All counters take explicit numerators and denominators; abstention is never
folded into a silent reject.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

GRANT = "grant_if_eligible"


def false_award_metrics(
    *,
    grants_by_dedup_key: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    """Duplicate-grant audit over content-identical submissions.

    ``grants_by_dedup_key`` maps each dedup key to the case IDs that received a
    grant for it. Exactly one grant per key is legitimate; anything beyond the
    first is a duplicate award (the LN-05 hard counterexample).
    """
    total_grants = 0
    duplicate_grants = 0
    keys_with_multiple: list[str] = []
    for key, cases in grants_by_dedup_key.items():
        n = len(list(cases))
        total_grants += n
        if n > 1:
            duplicate_grants += n - 1
            keys_with_multiple.append(key)
    return {
        "dedup_keys": len(grants_by_dedup_key),
        "total_grants": total_grants,
        "duplicate_grant_count": duplicate_grants,
        "keys_with_multiple_grants": sorted(keys_with_multiple),
    }


def security_utility_metrics(
    *,
    decisions: Mapping[str, str],
    replay_case_ids: Iterable[str],
    legit_eligible_case_ids: Iterable[str],
) -> dict[str, Any]:
    """FAR vs legitimate recall on labelled case populations.

    - ``false_award_rate``: grants among threat/replay deliveries.
    - ``legitimate_award_recall``: grants among legitimately eligible learners.
    """
    replay_ids = list(replay_case_ids)
    legit_ids = list(legit_eligible_case_ids)
    far_num = sum(1 for cid in replay_ids if decisions.get(cid) == GRANT)
    recall_num = sum(1 for cid in legit_ids if decisions.get(cid) == GRANT)
    far = far_num / len(replay_ids) if replay_ids else None
    recall = recall_num / len(legit_ids) if legit_ids else None
    return {
        "false_award_rate": far,
        "false_award_numerator": far_num,
        "false_award_denominator": len(replay_ids),
        "legitimate_award_recall": recall,
        "legitimate_award_recall_numerator": recall_num,
        "legitimate_award_recall_denominator": len(legit_ids),
    }


def confusion(decisions: Mapping[str, str], gold: Mapping[str, str]) -> dict[str, int]:
    """Paired confusion counts ``gold->pred`` plus per-class totals.

    Requires exactly the same case population on both sides; raises on any
    mismatch so silent exclusion cannot inflate scores.
    """
    if set(decisions) != set(gold):
        missing = sorted(set(gold) - set(decisions))
        extra = sorted(set(decisions) - set(gold))
        raise ValueError(f"case population mismatch; missing={missing[:5]} extra={extra[:5]}")
    counts: Counter[tuple[str, str]] = Counter()
    for case_id, gold_label in gold.items():
        counts[(gold_label, decisions[case_id])] += 1
    correct = sum(n for (g, p), n in counts.items() if g == p)
    return {
        **{f"{g}->{p}": n for (g, p), n in sorted(counts.items())},
        "n_total": len(gold),
        "n_correct": correct,
        "accuracy": (correct / len(gold)) if gold else None,
    }
