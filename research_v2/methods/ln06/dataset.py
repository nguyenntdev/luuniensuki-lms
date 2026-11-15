"""LN-06 dataset loading, schema validation and sealed-split resolution.

The inference-time feature schema for one case (the ``input`` subtree of the
T3 holdout fixtures):

    stops                       : list of {id, cost, provides, requires, type}
    available_stops             : subset of stop ids open to the learner
    target_outcomes             : pedagogical outcomes that must be covered
    time_budget_minutes         : total dwell+travel budget
    checkpoint_claim_verified   : source-authenticity gate flag
    learner                     : profile metadata (never used by policies)
    seed                        : scenario generation seed (tie-breaking only)

Any invalid row rejects the whole batch with its location - never a guessed
fallback value.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class DatasetError(ValueError):
    """Raised when a dataset row violates the LN-06 input schema."""


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "research_v2" / "data" / "ln06" / "t3_inputs.jsonl"
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln06" / "t3_gold.jsonl"
STUDY_ID = "LN-06"


@dataclass(frozen=True)
class Stop:
    id: str
    cost: int
    provides: tuple[str, ...]
    requires: tuple[str, ...]
    type: str = "imperial-site"

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "Stop":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: stop must be a mapping, got {type(raw).__name__}")
        sid = raw.get("id")
        if not isinstance(sid, str) or not sid:
            raise DatasetError(f"{location}: stop.id must be a non-empty string")
        cost = raw.get("cost")
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
            raise DatasetError(f"{location}: stop {sid!r} cost must be a non-negative number")
        provides = raw.get("provides", [])
        requires = raw.get("requires", [])
        if not isinstance(provides, list) or not all(isinstance(o, str) and o for o in provides):
            raise DatasetError(f"{location}: stop {sid!r} provides must be a list of non-empty strings")
        if not isinstance(requires, list) or not all(isinstance(o, str) and o for o in requires):
            raise DatasetError(f"{location}: stop {sid!r} requires must be a list of non-empty strings")
        stype = raw.get("type", "imperial-site")
        if not isinstance(stype, str):
            raise DatasetError(f"{location}: stop {sid!r} type must be a string")
        return cls(
            id=sid,
            cost=int(cost),
            provides=tuple(dict.fromkeys(provides)),
            requires=tuple(dict.fromkeys(requires)),
            type=stype,
        )


@dataclass(frozen=True)
class TravelEdge:
    source: str
    target: str
    minutes: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "TravelEdge":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: travel edge must be a mapping")
        src, dst, mins = raw.get("from"), raw.get("to"), raw.get("minutes")
        if not isinstance(src, str) or not src or not isinstance(dst, str) or not dst:
            raise DatasetError(f"{location}: travel edge needs non-empty 'from'/'to' stop ids")
        if not isinstance(mins, (int, float)) or isinstance(mins, bool) or mins < 0:
            raise DatasetError(f"{location}: travel edge {src}->{dst} minutes must be non-negative")
        return cls(source=src, target=dst, minutes=int(mins))


@dataclass(frozen=True)
class TrailCase:
    """Validated, oracle-free view of one LN-06 case."""

    case_id: str
    stops: tuple[Stop, ...]
    available_stops: frozenset[str]
    target_outcomes: frozenset[str]
    time_budget_minutes: int
    checkpoint_claim_verified: bool
    travel_edges: tuple[TravelEdge, ...] = ()

    @classmethod
    def from_features(cls, features: Mapping[str, Any], *, case_id: str) -> "TrailCase":
        location = f"case {case_id!r}"
        if not isinstance(features, Mapping):
            raise DatasetError(f"{location}: features must be a mapping")
        raw_stops = features.get("stops")
        if not isinstance(raw_stops, list) or not raw_stops:
            raise DatasetError(f"{location}: stops must be a non-empty list")
        stops = tuple(
            Stop.from_dict(s, location=f"{location} stops[{i}]") for i, s in enumerate(raw_stops)
        )
        ids = [s.id for s in stops]
        if len(set(ids)) != len(ids):
            raise DatasetError(f"{location}: duplicate stop ids in {ids}")

        available = features.get("available_stops")
        if not isinstance(available, list) or not all(isinstance(a, str) for a in available):
            raise DatasetError(f"{location}: available_stops must be a list of stop ids")
        unknown = sorted(set(available) - set(ids))
        if unknown:
            raise DatasetError(f"{location}: available_stops reference unknown ids {unknown}")

        targets = features.get("target_outcomes")
        if not isinstance(targets, list) or not all(isinstance(t, str) and t for t in targets):
            raise DatasetError(f"{location}: target_outcomes must be a list of outcome names")

        budget = features.get("time_budget_minutes")
        if not isinstance(budget, (int, float)) or isinstance(budget, bool) or budget < 0:
            raise DatasetError(f"{location}: time_budget_minutes must be a non-negative number")

        verified = features.get("checkpoint_claim_verified")
        if not isinstance(verified, bool):
            raise DatasetError(f"{location}: checkpoint_claim_verified must be a boolean")

        raw_edges = features.get("travel_edges", []) or []
        if not isinstance(raw_edges, list):
            raise DatasetError(f"{location}: travel_edges must be a list")
        edges = tuple(
            TravelEdge.from_dict(e, location=f"{location} travel_edges[{i}]")
            for i, e in enumerate(raw_edges)
        )
        known = set(ids)
        for e in edges:
            if e.source not in known or e.target not in known:
                raise DatasetError(
                    f"{location}: travel edge {e.source}->{e.target} references unknown stop ids"
                )
        return cls(
            case_id=case_id,
            stops=stops,
            available_stops=frozenset(available),
            target_outcomes=frozenset(targets),
            time_budget_minutes=int(budget),
            checkpoint_claim_verified=verified,
            travel_edges=edges,
        )

    def stop_by_id(self) -> dict[str, Stop]:
        return {s.id: s for s in self.stops}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise DatasetError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def load_t3_cases() -> list[TrailCase]:
    """Load and validate every T3 holdout input row (oracle-free)."""
    cases: list[TrailCase] = []
    for row in load_jsonl(DATASET_PATH):
        case_id = row.get("case_id")
        if not case_id:
            raise DatasetError("input row missing case_id")
        cases.append(TrailCase.from_features(row["input"], case_id=str(case_id)))
    return cases


def load_gold() -> dict[str, str]:
    """Evaluator-side only: case_id -> expected decision."""
    gold: dict[str, str] = {}
    for row in load_jsonl(GOLD_PATH):
        cid = row.get("case_id")
        dec = row.get("expected_decision")
        if not cid or not dec:
            raise DatasetError("gold row missing case_id/expected_decision")
        gold[str(cid)] = str(dec)
    return gold
