"""P02 — Constraint-Aware Learning Path Planning with Alternative Activities.

Modules:
- ``problems``    : typed planning instances (activities, outcomes, travel, accessibility).
- ``generator``   : deterministic randomised instances across topology families,
                    budget regimes and alternative-provider densities.
- ``oracle``      : INDEPENDENT brute-force feasibility/cost certification
                    (evaluator-side only; never imported by a solver).
- ``solvers``     : C0 greedy, C1 branch-and-bound, C2 Dijkstra-with-state,
                    proposed A* planner, A3 alternative-blind ablation.
- ``metrics``     : feasibility rate, optimality gap, false infeasibility, runtime.
- ``benchmark``   : CLI running the full >=500-instance matrix into artifacts.
"""
from __future__ import annotations

PAPER_ID = "P02"
METHOD_ID = "p02-proposed"
METHOD_VERSION = "p02-proposed-v1.0"

__all__ = [
    "PAPER_ID",
    "METHOD_ID",
    "METHOD_VERSION",
]
