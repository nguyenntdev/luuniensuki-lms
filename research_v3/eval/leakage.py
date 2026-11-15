"""Leakage audit: detect future information, duplicate sources and gold leaks.

Runs on a materialized dataset BEFORE any training. A single finding fails the
audit (fail-closed), because a leak invalidates every downstream metric.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

GOLD_KEYS = frozenset(
    {
        "oracle",
        "expected_decision",
        "expected_outcome",
        "expected_conclusion",
        "gold",
        "gold_label",
        "label",
        "labels",
        "fault_id",
        "cohort",
        "is_correct",
        "correct",
    }
)

FUTURE_HINTS = ("after_cutoff", "future_", "post_test", "final_grade_after")


class LeakageError(ValueError):
    """Raised when the leakage audit finds a contamination path."""


def _walk_keys(node: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            yield str(key), here
            yield from _walk_keys(value, here)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from _walk_keys(value, f"{path}[{idx}]")


def audit_rows(rows: Iterable[Mapping[str, Any]], *, strict: bool = True) -> dict[str, Any]:
    """Return an audit report; raise ``LeakageError`` on any finding in strict mode."""
    findings: list[str] = []
    seen_ids: set[str] = set()
    duplicates = 0
    n = 0
    for n, row in enumerate(rows, 1):
        cid = str(row.get("case_id", ""))
        if cid:
            if cid in seen_ids:
                duplicates += 1
                findings.append(f"row {n}: duplicate case_id {cid!r}")
            seen_ids.add(cid)
        for key, dotted in _walk_keys(row.get("input", row)):
            if key in GOLD_KEYS:
                findings.append(f"row {n}: gold key {key!r} inside model input at {dotted}")
            if any(hint in key.lower() for hint in FUTURE_HINTS):
                findings.append(f"row {n}: possible future-information key {key!r} at {dotted}")
    report = {
        "rows": n,
        "duplicates": duplicates,
        "unique_case_ids": len(seen_ids),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }
    if strict and findings:
        raise LeakageError(f"leakage audit failed with {len(findings)} finding(s): {findings[:5]}")
    return report


def assert_disjoint_groups(
    train: Iterable[Mapping[str, Any]],
    test: Iterable[Mapping[str, Any]],
    *,
    group_key: str,
) -> None:
    """Fail when a grouping key (learner/course/monument) spans train and test."""
    train_groups = {str(r[group_key]) for r in train if group_key in r}
    test_groups = {str(r[group_key]) for r in test if group_key in r}
    overlap = train_groups & test_groups
    if overlap:
        raise LeakageError(
            f"{len(overlap)} group(s) span train and test, e.g. {sorted(overlap)[:5]}"
        )
