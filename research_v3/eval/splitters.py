"""Strict group/time splitter with leakage guards.

Every split is materialized once and hashed; train/calibration/dev/test must be
disjoint on the declared grouping key. A subsequent run re-materializes the same
split from the same frozen manifest and must reproduce the identical hash.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping, Sequence

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.contracts.cards import ContractError, FrozenSplit


class SplitError(ContractError):
    """Raised when a split would leak groups across partitions."""


def _stable_bucket(key: str, buckets: int, salt: str) -> int:
    digest = hashlib.sha256(f"{salt}:{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % buckets


def group_split(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_key: str,
    paper_id: str,
    protocol: str = "group",
    fractions: tuple[float, float, float, float] = (0.70, 0.10, 0.10, 0.10),
    salt: str = "v3",
) -> FrozenSplit:
    """Deterministically split by ``group_key`` into train/calibration/dev/test.

    Rows sharing a ``group_key`` always land in the same partition, so no
    learner/course/monument can appear in two partitions.
    """
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise SplitError(f"fractions must sum to 1.0, got {sum(fractions)}")
    if not rows:
        raise SplitError("cannot split an empty dataset")

    group_to_part: dict[str, str] = {}
    buckets = 10_000
    train_end = fractions[0] * buckets
    cal_end = train_end + fractions[1] * buckets
    dev_end = cal_end + fractions[2] * buckets

    for row in rows:
        if group_key not in row:
            raise SplitError(f"row missing group key {group_key!r}")
        gid = str(row[group_key])
        if gid in group_to_part:
            continue
        pos = _stable_bucket(gid, buckets, salt)
        if pos < train_end:
            group_to_part[gid] = "train"
        elif pos < cal_end:
            group_to_part[gid] = "calibration"
        elif pos < dev_end:
            group_to_part[gid] = "dev"
        else:
            group_to_part[gid] = "test"

    splits: dict[str, list[str]] = {"train": [], "calibration": [], "dev": [], "test": []}
    for row in rows:
        gid = str(row[group_key])
        splits[group_to_part[gid]].append(str(row.get("case_id", gid)))

    for name, ids in splits.items():
        if not ids:
            raise SplitError(
                f"{paper_id}: partition {name!r} is empty; adjust fractions or group key"
            )
    return FrozenSplit(
        paper_id=paper_id,
        protocol=protocol,
        split_ids={k: tuple(v) for k, v in splits.items()},
    )


def time_split(
    rows: Sequence[Mapping[str, Any]],
    *,
    time_key: str,
    paper_id: str,
    train_fraction: float = 0.70,
) -> FrozenSplit:
    """Chronological split: train on the past, test on the future, no leakage."""
    if not rows:
        raise SplitError("cannot split an empty dataset")
    ordered = sorted(rows, key=lambda r: r[time_key])
    n = len(ordered)
    train_end = int(n * train_fraction)
    remaining = n - train_end
    cal = train_end + int(remaining * 0.34)
    dev = cal + int(remaining * 0.33)

    def ids(seq: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
        return tuple(str(r.get("case_id", idx)) for idx, r in enumerate(seq))

    splits = {
        "train": ids(ordered[:train_end]),
        "calibration": ids(ordered[train_end:cal]),
        "dev": ids(ordered[cal:dev]),
        "test": ids(ordered[dev:]),
    }
    for name, part in splits.items():
        if not part:
            raise SplitError(f"{paper_id}: time partition {name!r} is empty")
    return FrozenSplit(paper_id=paper_id, protocol="time", split_ids=splits)


def freeze_hash(split: FrozenSplit) -> str:
    """Deterministic hash of the frozen split for the experiment card."""
    return sha256_input(split.to_dict())


def assert_no_leakage(split: FrozenSplit) -> None:
    """Fail when any id appears in more than one partition."""
    seen: dict[str, str] = {}
    for name, ids in split.split_ids.items():
        for ident in ids:
            if ident in seen:
                raise SplitError(
                    f"{split.paper_id}: id {ident!r} appears in both "
                    f"{seen[ident]!r} and {name!r}"
                )
            seen[ident] = name
