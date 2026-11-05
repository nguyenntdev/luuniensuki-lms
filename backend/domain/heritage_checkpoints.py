# -*- coding: utf-8 -*-
"""Domain entities and contracts for LN-06 heritage checkpoints and cognitive trails.

Pure domain dataclasses and validation functions for:
- HeritageStop: Represents a site stop with cost, provided outcomes, and prerequisites
- LearningCheckpoint: Checkpoint task, evidence requirements, unlock status
- RouteObjective: Competencies, time budget, modality constraints
- RoutePlan: Computed route, stop sequence, violations, reasons
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class HeritageStop:
    """Represents a heritage site stop in a learning trail."""
    id: str
    cost: int
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    label: str = ""
    site_type: str = "imperial-site"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeritageStop:
        return cls(
            id=str(data.get("id", "")),
            cost=int(data.get("cost", 0)),
            provides=list(data.get("provides", [])),
            requires=list(data.get("requires", [])),
            label=str(data.get("label", "")),
            site_type=str(data.get("type", data.get("site_type", "imperial-site"))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cost": self.cost,
            "provides": list(self.provides),
            "requires": list(self.requires),
            "label": self.label,
            "site_type": self.site_type,
        }


@dataclass(frozen=True)
class LearningCheckpoint:
    """Represents a pedagogical checkpoint on a trail."""
    id: str
    task_type: str = "observation"
    required_evidence_ids: list[str] = field(default_factory=list)
    unlock_conditions: list[str] = field(default_factory=list)
    claim_verified: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningCheckpoint:
        return cls(
            id=str(data.get("id", "")),
            task_type=str(data.get("task_type", "observation")),
            required_evidence_ids=list(data.get("required_evidence_ids", [])),
            unlock_conditions=list(data.get("unlock_conditions", [])),
            claim_verified=bool(data.get("claim_verified", True)),
        )


@dataclass(frozen=True)
class RouteObjective:
    """Represents the pedagogical constraints and learning goals for a route."""
    target_outcomes: list[str]
    time_budget_minutes: int
    available_stops: list[str]
    checkpoint_claim_verified: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteObjective:
        return cls(
            target_outcomes=list(data.get("target_outcomes", [])),
            time_budget_minutes=int(data.get("time_budget_minutes", 0)),
            available_stops=list(data.get("available_stops", [])),
            checkpoint_claim_verified=bool(data.get("checkpoint_claim_verified", True)),
        )


@dataclass(frozen=True)
class RoutePlan:
    """Computed plan result for a trail route."""
    decision: str
    reason_codes: list[str]
    stop_sequence: list[str] = field(default_factory=list)
    route_cost: int = 0
    outcome_coverage: float = 0.0
    prerequisite_violation_count: int = 0
    unreachable_checkpoint_rate: float = 0.0
    policy_version: str = "LN-06-v1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "stop_sequence": list(self.stop_sequence),
            "route_cost": self.route_cost,
            "outcome_coverage": self.outcome_coverage,
            "prerequisite_violation_count": self.prerequisite_violation_count,
            "unreachable_checkpoint_rate": self.unreachable_checkpoint_rate,
            "policy_version": self.policy_version,
            "research_only": True,
        }
