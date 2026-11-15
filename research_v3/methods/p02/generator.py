"""P02 deterministic instance generator with topology families and regimes.

Families (the group key for leakage-safe splits — every instance from one
family template lands in exactly one partition):

- ``chain``             : prerequisite path, one provider per outcome.
- ``alternative_pair``  : the LN-06 stress shape — some outcomes have 2+
                          interchangeable providers (mandatory A/B semantics).
- ``dense_cover``       : overlapping multi-outcome activities (set-cover-like).
- ``unreachable_bridge``: a target whose only provider chain is broken.
- ``mixed_lattice``     : layered DAG with cross-layer alternatives.
- ``blocked_access``    : feasible except the only provider is inaccessible or
                          below the source-authenticity floor.

Budget regimes set the budget as a multiple of the oracle-known optimum:
- ``tight``  : budget = optimum + small slack (cost_exceeded pressure)
- ``mid``    : budget = 1.2x optimum
- ``loose``  : budget = 2.0x optimum

Alternative-provider density (0.0..1.0) controls how many outcomes get a
second interchangeable provider.

Every instance is small enough for the independent brute-force oracle, so the
known optimum is CERTIFIED (never fabricated): generator calls the oracle and
records the certified cost with the instance. Determinism: per-instance
``random.Random`` seeded from (family, regime, seed, index); no global RNG.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .oracle import OracleError, OracleVerdict, brute_force_verdict
from .problems import Activity, PlanningProblem

TOPOLOGY_FAMILIES = (
    "chain",
    "alternative_pair",
    "dense_cover",
    "unreachable_bridge",
    "mixed_lattice",
    "blocked_access",
)
BUDGET_REGIMES = ("tight", "mid", "loose")

_REGIME_SLACK = {"tight": (2, 8), "mid": (10, 30), "loose": (60, 120)}


@dataclass(frozen=True)
class GeneratedCase:
    problem: PlanningProblem
    oracle: OracleVerdict  # certified optimum — evaluator-side provenance
    regime: str
    alt_density: float
    n_activities: int
    n_targets: int
    alt_outcomes: int  # number of outcomes with >= 2 interchangeable providers


def _rng(family: str, regime: str, seed: int, index: int) -> random.Random:
    return random.Random(f"p02|{family}|{regime}|{seed}|{index}")


def _travel_matrix(
    rng: random.Random, ids: list[str], density: float, asymmetric: bool
) -> dict[tuple[str, str], int]:
    travel: dict[tuple[str, str], int] = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if rng.random() < density:
                m = rng.randrange(0, 15)
                travel[(a, b)] = m
                travel[(b, a)] = rng.randrange(0, 15) if asymmetric else m
    return travel


def _alternative_provider_count(problem: PlanningProblem) -> int:
    providers: dict[str, int] = {}
    for a in problem.activities:
        for o in a.provides:
            providers[o] = providers.get(o, 0) + 1
    return sum(1 for o in problem.targets if providers.get(o, 0) >= 2)


def _build_base(
    rng: random.Random,
    family: str,
    alt_density: float,
    *,
    n_chain: int,
    alt_target_slots: int,
    cover_size: int,
) -> tuple[list[Activity], list[str]]:
    """Family-specific activity construction; returns (activities, targets)."""
    activities: list[Activity] = []
    targets: list[str] = []
    counter = {"i": 0}

    def new_id(prefix: str) -> str:
        counter["i"] += 1
        return f"{prefix}_{counter['i']:02d}"

    def alt_slot(outcome: str, requires: tuple[str, ...]) -> None:
        """Add an interchangeable provider of ``outcome`` when density allows."""
        if rng.random() >= alt_density:
            return
        activities.append(
            Activity(
                id=new_id("alt"),
                cost=rng.randrange(15, 45),
                provides=(outcome,),
                requires=requires,
            )
        )

    if family == "chain":
        prev: tuple[str, ...] = ()
        for k in range(n_chain):
            o = f"O{k}"
            sid = new_id("act")
            activities.append(
                Activity(id=sid, cost=rng.randrange(15, 40), provides=(o,), requires=prev)
            )
            alt_slot(o, prev)
            prev = (o,)
        targets = [f"O{n_chain - 1}"]

    elif family == "alternative_pair":
        prev: tuple[str, ...] = ()
        reqs_by_outcome: dict[str, tuple[str, ...]] = {}
        for k in range(n_chain):
            o = f"O{k}"
            sid = new_id("act")
            activities.append(
                Activity(id=sid, cost=rng.randrange(30, 45), provides=(o,), requires=prev)
            )
            reqs_by_outcome[o] = prev
            prev = (o,)
        targets = [f"O{k}" for k in range(n_chain)]
        # Mandatory alternative shape: an interchangeable provider of the
        # FINAL outcome at near-identical cost, with the SAME prerequisites
        # as the primary provider (never a self-cycle).
        for _ in range(max(1, alt_target_slots)):
            o = targets[-1]
            activities.append(
                Activity(
                    id=new_id("altb"),
                    cost=max(1, activities[-1].cost + rng.randrange(-5, 6)),
                    provides=(o,),
                    requires=reqs_by_outcome[o],
                )
            )

    elif family == "dense_cover":
        n_out = n_chain
        outcomes = [f"O{k}" for k in range(n_out)]
        targets = outcomes[:]
        for o in outcomes:
            sid = new_id("act")
            activities.append(Activity(id=sid, cost=rng.randrange(20, 45), provides=(o,), requires=()))
            alt_slot(o, ())
        for _ in range(cover_size):
            span = rng.sample(outcomes, k=min(len(outcomes), rng.randrange(2, 4)))
            activities.append(
                Activity(id=new_id("cov"), cost=rng.randrange(35, 60), provides=tuple(span), requires=())
            )

    elif family == "unreachable_bridge":
        prev: tuple[str, ...] = ()
        for k in range(max(2, n_chain - 1)):
            o = f"O{k}"
            sid = new_id("act")
            activities.append(
                Activity(id=sid, cost=rng.randrange(15, 40), provides=(o,), requires=prev)
            )
            prev = (o,)
        # Broken bridge: target with NO provider at all.
        targets = [f"O{n_chain - 1}", "OB"]

    elif family == "mixed_lattice":
        layers = 3
        width = max(2, n_chain // 2)
        layer_outcomes: list[list[str]] = []
        for l in range(layers):
            row: list[str] = []
            for w in range(width):
                o = f"L{l}W{w}"
                sid = new_id("lat")
                reqs = tuple(layer_outcomes[l - 1]) if l > 0 else ()
                activities.append(
                    Activity(id=sid, cost=rng.randrange(15, 40), provides=(o,), requires=reqs)
                )
                alt_slot(o, reqs)
                row.append(o)
            layer_outcomes.append(row)
        targets = rng.sample(layer_outcomes[-1], k=max(1, width - 1))

    elif family == "blocked_access":
        prev: tuple[str, ...] = ()
        for k in range(n_chain):
            o = f"O{k}"
            sid = new_id("act")
            activities.append(
                Activity(id=sid, cost=rng.randrange(15, 40), provides=(o,), requires=prev)
            )
            prev = (o,)
        targets = [f"O{n_chain - 1}"]
        if rng.random() < 0.5:
            activities[-1] = Activity(
                id=activities[-1].id,
                cost=activities[-1].cost,
                provides=activities[-1].provides,
                requires=activities[-1].requires,
                accessible=False,
            )
        else:
            activities[-1] = Activity(
                id=activities[-1].id,
                cost=activities[-1].cost,
                provides=activities[-1].provides,
                requires=activities[-1].requires,
                source_tier="unverified",
            )

    return activities, targets


def generate_case(
    *,
    family: str,
    regime: str,
    seed: int,
    index: int,
    alt_density: float = 0.5,
    with_travel: bool = True,
    require_accessible: bool = True,
) -> GeneratedCase:
    """Build one certified instance; raises ValueError on unknown axes."""
    if family not in TOPOLOGY_FAMILIES:
        raise ValueError(f"unknown family {family!r}; known: {TOPOLOGY_FAMILIES}")
    if regime not in BUDGET_REGIMES:
        raise ValueError(f"unknown regime {regime!r}; known: {BUDGET_REGIMES}")
    if not 0.0 <= alt_density <= 1.0:
        raise ValueError("alt_density must be within [0, 1]")
    rng = _rng(family, regime, seed, index)

    n_chain = rng.randrange(3, 6)  # 3..5 outcome chain (oracle-safe size)
    activities, targets = _build_base(
        rng, family, alt_density, n_chain=n_chain, alt_target_slots=1, cover_size=2
    )
    if len(activities) > 9:  # oracle envelope
        activities = activities[:9]

    ids = [a.id for a in activities]
    travel = _travel_matrix(rng, ids, density=0.35 if with_travel else 0.0,
                            asymmetric=rng.random() < 0.5) if with_travel else {}

    problem_id = f"p02-{family}-{regime}-d{round(alt_density, 2)}-s{seed}-{index:04d}"
    problem = PlanningProblem(
        problem_id=problem_id,
        family_id=f"{family}|d{round(alt_density, 2)}",
        activities=tuple(activities),
        targets=frozenset(targets),
        budget=10**6,  # placeholder; set from certified optimum below
        travel=travel,
        require_accessible=require_accessible,
    )
    try:
        verdict = brute_force_verdict(problem)
    except OracleError as exc:  # pragma: no cover - envelope guard above
        raise RuntimeError(f"generator produced an oracle-oversized instance: {exc}") from exc

    lo, hi = _REGIME_SLACK[regime]
    if verdict.optimum_cost is None:
        budget = rng.randrange(40, 120)
    elif regime == "tight" and rng.random() < 0.35:
        # Tight regime intentionally includes below-optimum budgets so the
        # cost_exceeded gold stratum is genuinely represented (fail-closed
        # honesty: infeasible-by-budget instances exist in the benchmark).
        budget = max(0, verdict.optimum_cost - rng.randrange(1, 25))
    else:
        budget = verdict.optimum_cost + rng.randrange(lo, hi + 1)
    problem = PlanningProblem(
        problem_id=problem_id,
        family_id=f"{family}|d{round(alt_density, 2)}",
        activities=tuple(activities),
        targets=frozenset(targets),
        budget=budget,
        travel=travel,
        require_accessible=require_accessible,
    )
    # The budget CHANGED after the first verdict: re-certify against the
    # final instance so the stored oracle verdict is never stale (fail-closed
    # honesty — an optimum recorded for a different budget would be a
    # fabricated ground truth).
    verdict = brute_force_verdict(problem)
    return GeneratedCase(
        problem=problem,
        oracle=verdict,
        regime=regime,
        alt_density=alt_density,
        n_activities=len(activities),
        n_targets=len(targets),
        alt_outcomes=_alternative_provider_count(problem),
    )


def generate_matrix(
    *,
    seed: int,
    instances_per_cell: int,
    regimes: tuple[str, ...] = BUDGET_REGIMES,
    families: tuple[str, ...] = TOPOLOGY_FAMILIES,
    alt_densities: tuple[float, ...] = (0.0, 0.5, 1.0),
) -> list[GeneratedCase]:
    """Full randomised matrix: families x regimes x densities x replications."""
    cases: list[GeneratedCase] = []
    for family in families:
        for regime in regimes:
            for density in alt_densities:
                for i in range(instances_per_cell):
                    cases.append(
                        generate_case(
                            family=family,
                            regime=regime,
                            seed=seed,
                            index=i,
                            alt_density=density,
                        )
                    )
    return cases
