"""P04 stratum S2: annotation-budget bridge over REAL unseen platform categories.

Instead of synthesizing "unknown" edges, S2 restricts the verified-edge
annotation budget to the train-partition courses. Platform categories that
occur in test-partition courses but never in train courses become REAL unknown
edges: the bridge cannot map them, mapping coverage drops, and every affected
test case is recorded as NOT_APPLICABLE — never silently imputed.

This is a real, reproducible property of the frozen OULAD snapshot: courses
genuinely expose different resource-type mixes (e.g. AAA has no `quiz` sites).
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from research_v3.methods.p04.bridge import OntologyBridge, bridge_from_oulad


def activity_type_counts(rows: Sequence[Mapping[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        atype = row["input"].get("activity_type", "")
        if atype:
            counts[atype] += 1
    return counts


def bridge_within_annotation_budget(
    train_rows: Sequence[Mapping[str, Any]],
    test_rows: Sequence[Mapping[str, Any]],
) -> tuple[OntologyBridge, dict[str, Any]]:
    """Build the bridge from train rows only; report real test-side unknowns.

    Returns (bridge, audit) where audit lists the platform categories that
    appear in test data but were outside the annotation budget. The bridge is
    a faithful learner of a REAL constraint: annotators see only the courses
    they are given.
    """
    bridge = bridge_from_oulad(activity_type_counts(train_rows))
    test_counts = activity_type_counts(test_rows)
    unknown_in_test = sorted(
        atype for atype in test_counts if atype not in bridge.edges or bridge.edges[atype].status != "verified"
    )
    affected = sum(test_counts[atype] for atype in unknown_in_test)
    total = sum(test_counts.values())
    audit = {
        "train_annotation_courses_basis": len(train_rows),
        "test_categories_total": sorted(test_counts),
        "unknown_in_test": unknown_in_test,
        "affected_test_rows": affected,
        "test_rows": total,
        "mapping_coverage_expected": round((total - affected) / total, 6) if total else 0.0,
    }
    return bridge, audit
