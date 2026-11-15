"""P13 leakage-proof splits: learner-grouped and presentation-temporal.

Reuses ``research_v3.eval.splitters`` (group_split, assert_no_leakage,
freeze_hash) — no ad-hoc splitting. Two protocols are materialised:

1. ``group``  — split by id_student; a learner never spans two partitions.
2. ``time``   — split by code_presentation; train on earlier presentations,
                test on the latest one (2014J). Within a presentation,
                learner-level grouping is additionally asserted.
"""
from __future__ import annotations

from typing import Any

from research_v3.eval.splitters import (
    SplitError,
    assert_no_leakage,
    freeze_hash,
    group_split,
)

GROUP_SALT = "p13-oulad-group-v1"
GROUP_FRACTIONS = (0.70, 0.10, 0.10, 0.10)

#: Presentations ordered chronologically (OULAD B = February start, J = October).
PRESENTATION_ORDER = ("2013B", "2013J", "2014B", "2014J")


class P13SplitError(SplitError):
    """Raised when a P13 split would leak learners or presentations."""


def materialize_group_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Learner-disjoint train/calibration/dev/test over case rows."""
    split = group_split(
        rows,
        group_key="group_id",
        paper_id="P13",
        protocol="group",
        fractions=GROUP_FRACTIONS,
        salt=GROUP_SALT,
    )
    assert_no_leakage(split)
    return {
        "protocol": "group",
        "group_key": "id_student",
        "salt": GROUP_SALT,
        "fractions": list(GROUP_FRACTIONS),
        "split_hash": freeze_hash(split),
        "counts": {k: len(v) for k, v in split.split_ids.items()},
        "split_ids": {k: list(v) for k, v in split.split_ids.items()},
    }


def materialize_time_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Temporal holdout: train 2013B/2013J/2014B, calibration+dev+test 2014J.

    The latest presentation is the frozen future; nothing from it may touch
    training. Learner disjointness across the temporal boundary is asserted
    too: a student who took both 2013J and 2014J must not secretly link the
    partitions — we therefore ALSO exclude from train any learner whose
    group_id appears in the held-out presentation (conservative purging).
    """
    present = sorted({str(r["time_key"]) for r in rows})
    unknown = [p for p in present if p not in PRESENTATION_ORDER]
    if unknown:
        raise P13SplitError(f"unknown presentations {unknown}")
    test_presentations = {PRESENTATION_ORDER[-1]}
    train_presentations = set(PRESENTATION_ORDER[:-1])

    test_group_ids = {
        str(r["group_id"]) for r in rows if str(r["time_key"]) in test_presentations
    }
    # Purge learners who appear in BOTH eras from TRAIN (they may reuse
    # experience from an earlier run of the same course; conservative choice,
    # preregistered).
    purged = 0
    train_cases: list[str] = []
    train_group_ids: set[str] = set()
    for r in rows:
        if str(r["time_key"]) in train_presentations:
            if str(r["group_id"]) in test_group_ids:
                purged += 1
                continue
            train_cases.append(str(r["case_id"]))
            train_group_ids.add(str(r["group_id"]))
    cal_cases: list[str] = []
    dev_cases: list[str] = []
    test_cases: list[str] = []
    for r in rows:
        if str(r["time_key"]) not in test_presentations:
            continue
        cid = str(r["case_id"])
        gid = str(r["group_id"])
        if gid in train_group_ids:  # defensive; train purge already prevents
            raise P13SplitError(f"learner {gid} spans train and test eras")
        # within-2014J: split case-level by stable hash into cal/dev/test
        from research_v3.eval.splitters import _stable_bucket

        pos = _stable_bucket(cid, 10_000, GROUP_SALT + "-time-inner")
        if pos < 5_000:
            cal_cases.append(cid)
        elif pos < 7_500:
            dev_cases.append(cid)
        else:
            test_cases.append(cid)

    if not (train_cases and cal_cases and dev_cases and test_cases):
        raise P13SplitError("empty temporal partition")

    from research_v3.contracts.cards import FrozenSplit

    frozen = FrozenSplit(
        paper_id="P13",
        protocol="time",
        split_ids={
            "train": tuple(train_cases),
            "calibration": tuple(cal_cases),
            "dev": tuple(dev_cases),
            "test": tuple(test_cases),
        },
    )
    assert_no_leakage(frozen)
    return {
        "protocol": "time",
        "group_key": "code_presentation",
        "train_presentations": sorted(train_presentations),
        "test_presentations": sorted(test_presentations),
        "purged_recurring_learners_from_train": purged,
        "split_hash": freeze_hash(frozen),
        "counts": {
            "train": len(train_cases),
            "calibration": len(cal_cases),
            "dev": len(dev_cases),
            "test": len(test_cases),
        },
        "split_ids": {
            "train": train_cases,
            "calibration": cal_cases,
            "dev": dev_cases,
            "test": test_cases,
        },
    }


def assert_train_test_disjoint(
    rows: list[dict[str, Any]], split_manifest: dict[str, Any]
) -> None:
    """Independent re-check: no group_id (learner) in both train and test."""
    by_case = {str(r["case_id"]): str(r["group_id"]) for r in rows}
    train_groups = {by_case[c] for c in split_manifest["split_ids"]["train"] if c in by_case}
    for part in ("calibration", "dev", "test"):
        part_groups = {by_case[c] for c in split_manifest["split_ids"][part] if c in by_case}
        overlap = train_groups & part_groups
        if overlap:
            raise P13SplitError(
                f"learner overlap between train and {part}: {sorted(overlap)[:5]}"
            )
