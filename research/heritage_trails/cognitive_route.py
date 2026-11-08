# -*- coding: utf-8 -*-
"""Cognitive Route Planning Engine for Study LN-06.

Hành trình ảo Đại Nội theo logic học tập và checkpoint có điều kiện.

Core capabilities:
1. Prerequisite Dependency Graph (DAG) construction & cycle detection.
2. Source confidence & claim verification gating (INV-LN-06-04).
3. Pedagogical target outcome coverage & reachability check.
4. Time budget constraint evaluation.
5. Topological sequence routing with minimal prerequisite violations.
6. Baseline spatial/naive routing and ablation configurations.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Optional, Sequence

from backend.domain.heritage_checkpoints import (
    HeritageStop,
    LearningCheckpoint,
    RouteObjective,
    RoutePlan,
)

POLICY_VERSION = "LN-06-cognitive-trails-v1.0"


def evaluate_route_intervention(
    stops: Sequence[HeritageStop],
    available_stops: Sequence[str],
    target_outcomes: Sequence[str],
    time_budget_minutes: int,
    checkpoint_claim_verified: bool = True,
    *,
    enforce_prerequisites: bool = True,
    enforce_budget: bool = True,
    enforce_reachability: bool = True,
    enforce_sources: bool = True,
) -> RoutePlan:
    """Intervention policy enforcing cognitive constraints, DAG dependencies, and budgets."""
    # 1. Source verification gate (INV-LN-06-04, RULE-LN-06-03)
    if enforce_sources and not checkpoint_claim_verified:
        return RoutePlan(
            decision="reject_checkpoint_source",
            reason_codes=["source_gap"],
            stop_sequence=[],
            route_cost=0,
            outcome_coverage=0.0,
            prerequisite_violation_count=0,
            unreachable_checkpoint_rate=0.0,
            policy_version=POLICY_VERSION,
        )

    # 2. Cycle detection in prerequisite structure (RULE-LN-06-04)
    if enforce_prerequisites:
        outcome_to_provider: dict[str, str] = {}
        for s in stops:
            for p in s.provides:
                outcome_to_provider[p] = s.id

        adj: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = defaultdict(int)
        all_ids = [s.id for s in stops]
        for sid in all_ids:
            in_degree[sid] = 0

        for s in stops:
            u = s.id
            for req in s.requires:
                if req in outcome_to_provider:
                    v = outcome_to_provider[req]
                    if v != u:
                        adj[v].append(u)
                        in_degree[u] += 1

        queue = deque([sid for sid in all_ids if in_degree[sid] == 0])
        visited_count = 0
        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(all_ids):
            return RoutePlan(
                decision="reject_cycle",
                reason_codes=["prerequisite_cycle"],
                stop_sequence=[],
                route_cost=0,
                outcome_coverage=0.0,
                prerequisite_violation_count=0,
                unreachable_checkpoint_rate=0.0,
                policy_version=POLICY_VERSION,
            )

    # 3. Check reachability of target outcomes and required prerequisites
    available_set = set(available_stops)
    target_set = set(target_outcomes)

    # Resolve required stops via transitive dependencies
    needed_outcomes = set(target_set)
    needed_stops: set[str] = set()
    added = True
    while added:
        added = False
        for s in stops:
            if s.id not in needed_stops:
                if any(p in needed_outcomes for p in s.provides):
                    needed_stops.add(s.id)
                    for req in s.requires:
                        needed_outcomes.add(req)
                    added = True

    if enforce_reachability:
        missing_needed = needed_stops - available_set
        provided_by_avail: set[str] = set()
        for s in stops:
            if s.id in available_set:
                provided_by_avail.update(s.provides)

        if missing_needed or not target_set.issubset(provided_by_avail):
            # Compute unreachable checkpoint rate
            total_req_stops = len(needed_stops) if needed_stops else len(stops)
            unreach_rate = len(missing_needed) / total_req_stops if total_req_stops > 0 else 1.0
            return RoutePlan(
                decision="no_feasible_route",
                reason_codes=["unreachable_stop"],
                stop_sequence=[],
                route_cost=0,
                outcome_coverage=len(target_set & provided_by_avail) / len(target_set) if target_set else 0.0,
                prerequisite_violation_count=0,
                unreachable_checkpoint_rate=round(unreach_rate, 4),
                policy_version=POLICY_VERSION,
            )

    # 4. Compute cost
    stops_to_visit = [s for s in stops if s.id in needed_stops]
    total_cost = sum(s.cost for s in stops_to_visit)

    if enforce_budget and total_cost > time_budget_minutes:
        return RoutePlan(
            decision="cost_exceeded",
            reason_codes=["over_budget"],
            stop_sequence=[],
            route_cost=total_cost,
            outcome_coverage=1.0,
            prerequisite_violation_count=0,
            unreachable_checkpoint_rate=0.0,
            policy_version=POLICY_VERSION,
        )

    # 5. Order stops via topological sort to satisfy prerequisites
    order_map = {s.id: s for s in stops_to_visit}
    in_deg: dict[str, int] = defaultdict(int)
    dep_adj: dict[str, list[str]] = defaultdict(list)
    for sid in order_map:
        in_deg[sid] = 0

    prov_map: dict[str, str] = {}
    for s in stops_to_visit:
        for p in s.provides:
            prov_map[p] = s.id

    for s in stops_to_visit:
        for req in s.requires:
            if req in prov_map:
                p_id = prov_map[req]
                if p_id != s.id and p_id in order_map:
                    dep_adj[p_id].append(s.id)
                    in_deg[s.id] += 1

    q = deque([sid for sid in order_map if in_deg[sid] == 0])
    ordered_sequence: list[str] = []
    while q:
        curr = q.popleft()
        ordered_sequence.append(curr)
        for nxt in dep_adj[curr]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                q.append(nxt)

    # Fallback to appending any remaining
    for sid in order_map:
        if sid not in ordered_sequence:
            ordered_sequence.append(sid)

    # Count prerequisite violations along ordered_sequence
    acquired_outcomes: set[str] = set()
    stop_lookup = {s.id: s for s in stops}
    violations = 0
    for sid in ordered_sequence:
        if sid in stop_lookup:
            s = stop_lookup[sid]
            for req in s.requires:
                if req not in acquired_outcomes:
                    violations += 1
            acquired_outcomes.update(s.provides)

    return RoutePlan(
        decision="find_valid_route",
        reason_codes=["nominal"],
        stop_sequence=ordered_sequence,
        route_cost=total_cost,
        outcome_coverage=1.0,
        prerequisite_violation_count=violations,
        unreachable_checkpoint_rate=0.0,
        policy_version=POLICY_VERSION,
    )


def evaluate_route_baseline(
    stops: Sequence[HeritageStop],
    available_stops: Sequence[str],
    target_outcomes: Sequence[str],
    time_budget_minutes: int,
    checkpoint_claim_verified: bool = True,
) -> RoutePlan:
    """Baseline policy: Naive spatial order (or reverse/input order).

    Ignores prerequisite DAG constraints, resulting in prerequisite violations.
    Does not verify source claims or budget limits rigorously.
    """
    # Baseline naive sequence: visits available stops in reverse or naive spatial order
    # (e.g. from inner court Cuu Dinh out to Ngo Mon, violating prerequisites)
    available_set = set(available_stops)
    target_set = set(target_outcomes)

    # Naive order: reverse of input stops that are in available_stops
    # In LN-06 fixtures, stops are ordered: ngo-mon, dien-thai-hoa, the-mieu, cuu-dinh
    # Reversing gives: cuu-dinh -> the-mieu -> dien-thai-hoa -> ngo-mon
    # This directly violates prerequisite order!
    naive_sequence = [s.id for s in reversed(stops) if s.id in available_set]
    total_cost = sum(s.cost for s in stops if s.id in naive_sequence)

    # Count prerequisite violations in naive_sequence
    # An outcome is acquired only after visiting the providing stop.
    acquired_outcomes: set[str] = set()
    stop_lookup = {s.id: s for s in stops}
    violations = 0

    for sid in naive_sequence:
        s = stop_lookup[sid]
        for req in s.requires:
            if req not in acquired_outcomes:
                violations += 1
        acquired_outcomes.update(s.provides)

    coverage = len(target_set & acquired_outcomes) / len(target_set) if target_set else 0.0

    # In baseline, it naively returns a route (find_valid_route) without noticing violations
    # or failing on cycle/budget/source, reflecting unconstrained naive routing.
    # As an observable, prerequisite_violation_count reflects the number of violations.
    return RoutePlan(
        decision="find_valid_route",
        reason_codes=["baseline_spatial_naive"],
        stop_sequence=naive_sequence,
        route_cost=total_cost,
        outcome_coverage=round(coverage, 4),
        prerequisite_violation_count=violations,
        unreachable_checkpoint_rate=0.0,
        policy_version="LN-06-baseline-v1.0",
    )


def evaluate_route_b1(
    stops: Sequence[HeritageStop],
    available_stops: Sequence[str],
    target_outcomes: Sequence[str],
    time_budget_minutes: int,
    checkpoint_claim_verified: bool = True,
) -> RoutePlan:
    """Stronger baseline B1: Greedy topological search without time-budget bounds.

    Attempts topological ordering to respect prerequisites where possible,
    but does NOT bound routes by time budget, does NOT reject unverified source
    claims, and fails to resolve cycles safely (appending remaining nodes).
    """
    available_set = set(available_stops)
    target_set = set(target_outcomes)

    avail_stops = [s for s in stops if s.id in available_set]
    order_map = {s.id: s for s in avail_stops}

    in_deg: dict[str, int] = defaultdict(int)
    dep_adj: dict[str, list[str]] = defaultdict(list)
    for sid in order_map:
        in_deg[sid] = 0

    prov_map: dict[str, str] = {}
    for s in avail_stops:
        for p in s.provides:
            prov_map[p] = s.id

    for s in avail_stops:
        for req in s.requires:
            if req in prov_map:
                p_id = prov_map[req]
                if p_id != s.id and p_id in order_map:
                    dep_adj[p_id].append(s.id)
                    in_deg[s.id] += 1

    q = deque([sid for sid in order_map if in_deg[sid] == 0])
    ordered_sequence: list[str] = []
    while q:
        curr = q.popleft()
        ordered_sequence.append(curr)
        for nxt in dep_adj[curr]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                q.append(nxt)

    for sid in order_map:
        if sid not in ordered_sequence:
            ordered_sequence.append(sid)

    total_cost = sum(s.cost for s in avail_stops if s.id in ordered_sequence)

    acquired_outcomes: set[str] = set()
    stop_lookup = {s.id: s for s in stops}
    violations = 0
    for sid in ordered_sequence:
        s = stop_lookup[sid]
        for req in s.requires:
            if req not in acquired_outcomes:
                violations += 1
        acquired_outcomes.update(s.provides)

    coverage = len(target_set & acquired_outcomes) / len(target_set) if target_set else 0.0

    return RoutePlan(
        decision="find_valid_route",
        reason_codes=["b1_greedy_topological_no_budget"],
        stop_sequence=ordered_sequence,
        route_cost=total_cost,
        outcome_coverage=round(coverage, 4),
        prerequisite_violation_count=violations,
        unreachable_checkpoint_rate=0.0,
        policy_version="LN-06-b1-v1.0",
    )

