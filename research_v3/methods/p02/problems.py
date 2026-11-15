"""P02 typed planning problems: activity hypergraph with alternative providers.

Formal statement (see METHOD.md). An instance is

- a finite set of activities a with integer dwell cost, a set of provided
  outcomes, a set of required outcomes, an accessibility flag and a
  source-authenticity tier;
- an asymmetric travel-time matrix over activities (0 when absent);
- a target outcome set that must ALL be acquired (by some chosen provider);
- a hard total budget (dwell + travel minutes);
- optional accessibility and authenticity constraints enforced by the solver
  (not baked into the cost), so ablations can disable them cleanly.

Key invariant alternative-provider semantics: an outcome is acquired when AT
LEAST ONE chosen activity provides it; selecting several providers of the
same outcome is never required and the optimum normally picks exactly one
(the LN-06 legacy false-infeasibility bug summed all providers instead).

``NOT_APPLICABLE`` (no constraint applies) and ``ABSTAIN`` (solver refuses to
return a plan) are distinct sentinel outcomes; they are never conflated with
a negative (infeasible) result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research_v3.contracts.cards import ContractError
from research_v2.contracts.canonical_hash import sha256_input

NOT_APPLICABLE = "NOT_APPLICABLE"
ABSTAIN = "ABSTAIN"

SOURCE_TIERS = frozenset({"verified", "review_pending", "unverified"})
DECISIONS = frozenset(
    {"find_valid_route", "no_feasible_route", "cost_exceeded", "abstain", ABSTAIN}
)
SOLVER_STATUSES = frozenset({"optimal", "bound_proven", "heuristic", "timeout", "abstain"})

DEFAULT_MAX_ACTIVITIES = 26  # brute-force / DP guardrails (2^26 worst case)


class ProblemError(ContractError):
    """Raised when a planning instance violates the P02 input schema."""


@dataclass(frozen=True)
class Activity:
    """One pedagogical activity node of the outcome hypergraph."""

    id: str
    cost: int  # dwell minutes, >= 0
    provides: tuple[str, ...]
    requires: tuple[str, ...]
    accessible: bool = True
    source_tier: str = "verified"

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ProblemError("activity.id must be a non-empty string")
        if not isinstance(self.cost, int) or self.cost < 0:
            raise ProblemError(f"{self.id}: cost must be a non-negative int")
        if any(not isinstance(o, str) or not o for o in (*self.provides, *self.requires)):
            raise ProblemError(f"{self.id}: outcomes must be non-empty strings")
        if self.source_tier not in SOURCE_TIERS:
            raise ProblemError(f"{self.id}: unknown source_tier {self.source_tier!r}")


@dataclass(frozen=True)
class PlanningProblem:
    """One fully validated P02 path-planning instance."""

    problem_id: str
    family_id: str  # topology family; group key for leakage-safe splits
    activities: tuple[Activity, ...]
    targets: frozenset[str]
    budget: int  # hard total budget (dwell + travel), minutes
    travel: Mapping[tuple[str, str], int]  # asymmetric minutes, >= 0
    require_accessible: bool = True
    min_source_tier: str = "verified"

    def __post_init__(self) -> None:
        if not self.problem_id:
            raise ProblemError("problem_id is required")
        if not self.family_id:
            raise ProblemError("family_id is required (group split key)")
        ids = [a.id for a in self.activities]
        if len(ids) != len(set(ids)):
            raise ProblemError(f"{self.problem_id}: duplicate activity ids")
        if isinstance(self.budget, bool) or not isinstance(self.budget, int) or self.budget < 0:
            raise ProblemError(f"{self.problem_id}: budget must be a non-negative int")
        if self.min_source_tier not in SOURCE_TIERS:
            raise ProblemError(f"{self.problem_id}: unknown min_source_tier {self.min_source_tier!r}")
        by_id = {a.id: a for a in self.activities}
        for (src, dst), minutes in self.travel.items():
            if src not in by_id or dst not in by_id:
                raise ProblemError(
                    f"{self.problem_id}: travel edge ({src!r}, {dst!r}) references unknown activity"
                )
            if not isinstance(minutes, int) or minutes < 0:
                raise ProblemError(
                    f"{self.problem_id}: travel ({src!r}, {dst!r}) must be a non-negative int"
                )
        frozen = dict(self.travel)
        object.__setattr__(self, "travel", _FrozenTravel(frozen))

    # -- canonical fingerprint -------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "family_id": self.family_id,
            "activities": [
                {
                    "id": a.id,
                    "cost": a.cost,
                    "provides": list(a.provides),
                    "requires": list(a.requires),
                    "accessible": a.accessible,
                    "source_tier": a.source_tier,
                }
                for a in self.activities
            ],
            "targets": sorted(self.targets),
            "budget": self.budget,
            "travel": {f"{s}->{d}": m for (s, d), m in sorted(self.travel.items())},
            "require_accessible": self.require_accessible,
            "min_source_tier": self.min_source_tier,
        }

    def sha256(self) -> str:
        return sha256_input(self.to_dict())

    # -- shared derived views --------------------------------------------------

    def by_id(self) -> dict[str, Activity]:
        return {a.id: a for a in self.activities}

    def usable_activities(self) -> tuple[Activity, ...]:
        """Activities that pass the accessibility and authenticity gates."""
        tier_rank = {"verified": 2, "review_pending": 1, "unverified": 0}
        floor = tier_rank[self.min_source_tier]
        return tuple(
            a
            for a in self.activities
            if (a.accessible or not self.require_accessible)
            and tier_rank[a.source_tier] >= floor
        )


class _FrozenTravel(Mapping[tuple[str, str], int]):
    """Read-only view guaranteeing the travel matrix is immutable after freeze."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[tuple[str, str], int]) -> None:
        self._data = data

    def __getitem__(self, key: tuple[str, str]) -> int:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: tuple[str, str], default: Any = None) -> Any:
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Mapping) and dict(self._data) == dict(other)

    def __hash__(self) -> int:  # pragma: no cover - deterministic content hash
        return hash(tuple(sorted(self._data.items())))


def travel_minutes(problem: PlanningProblem, src: str, dst: str) -> int:
    """Directed travel cost; missing edges cost 0 (same location convention)."""
    return problem.travel.get((src, dst), 0)


@dataclass(frozen=True)
class SolverResult:
    """Typed solver output; ``status`` is ALWAYS reported, never implied.

    status semantics (fail-closed ladder):
    - ``optimal``       : global optimum PROVEN by the solver itself
    - ``bound_proven``  : objective equal to a proven lower bound (certificate)
    - ``heuristic``     : feasible plan without any optimality claim
    - ``timeout``       : search budget exhausted; best-effort plan or ABSTAIN
    - ``abstain``       : solver refuses (e.g. oversized instance), NOT infeasible
    """

    problem_id: str
    solver_id: str
    decision: str  # find_valid_route | no_feasible_route | cost_exceeded | abstain
    status: str
    route: tuple[str, ...]
    total_cost: int
    dwell_cost: int
    travel_cost: int
    reason_codes: tuple[str, ...] = ()
    wall_ms: float = 0.0
    nodes_expanded: int = 0

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ProblemError(f"unknown decision {self.decision!r}")
        if self.status not in SOLVER_STATUSES:
            raise ProblemError(f"unknown solver status {self.status!r}")
        if self.decision == "find_valid_route" and self.status == "abstain":
            raise ProblemError("abstain cannot carry a plan")
        if self.decision != "find_valid_route" and self.route:
            raise ProblemError("non-feasible decisions must not carry a route")


def parse_problem(raw: Mapping[str, Any], *, location: str = "problem") -> PlanningProblem:
    """Parse and validate a raw mapping into a PlanningProblem (fail-closed)."""
    try:
        activities = tuple(
            Activity(
                id=str(a["id"]),
                cost=int(a["cost"]),
                provides=tuple(str(o) for o in a.get("provides", ())),
                requires=tuple(str(o) for o in a.get("requires", ())),
                accessible=bool(a.get("accessible", True)),
                source_tier=str(a.get("source_tier", "verified")),
            )
            for a in raw["activities"]
        )
        travel_raw = raw.get("travel") or {}
        if travel_raw and isinstance(next(iter(travel_raw)), str):
            travel = {
                (str(k).split("->")[0], str(k).split("->")[1]): int(v)
                for k, v in travel_raw.items()
            }
        else:
            travel = {(str(s), str(d)): int(m) for (s, d), m in travel_raw.items()}
        return PlanningProblem(
            problem_id=str(raw["problem_id"]),
            family_id=str(raw.get("family_id", raw["problem_id"])),
            activities=activities,
            targets=frozenset(str(t) for t in raw["targets"]),
            budget=int(raw["budget"]),
            travel=travel,
            require_accessible=bool(raw.get("require_accessible", True)),
            min_source_tier=str(raw.get("min_source_tier", "verified")),
        )
    except ProblemError:
        raise
    except Exception as exc:
        raise ProblemError(f"{location}: invalid problem payload ({exc})") from exc
