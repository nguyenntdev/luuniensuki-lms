# P02 — Constraint-Aware Learning Path Planning with Alternative Activities
# Manuscript skeleton (EC-TEL target; venue rank/fit is a human signoff, P02-T21).
# All numeric cells MUST be generated from research_artifacts_v3/runs/p02/ artifacts
# (render pipeline), never pasted by hand. Placeholders below are marked {{CELL:...}}.

status: SKELETON_CODE_READY   # not SCIENTIFIC_REVIEW_READY: external data BLOCKED (P02-T02..T06), human signoffs BLOCKED (P02-T19..T21)

title: "Constraint-Aware Learning Path Planning with Alternative Activities: A Certified Synthetic Benchmark and Honest Solver Status Reporting"

abstract_points:
  - "Learning-path planners must choose ONE among pedagogically equivalent alternative activities under hard budgets; a documented legacy engine summed all providers of the same outcome and falsely reported feasible plans infeasible."
  - "We formalize minimum-cost subset selection + ordering with alternatives, prerequisites, accessibility and source-authenticity gates, and prove the problem NP-hard (contains minimum-weight set cover even without travel)."
  - "We release a certified randomised benchmark ({{CELL:n_instances}} instances across 6 topology families, 3 budget regimes, 3 alternative-provider densities) whose ground truth is produced by an independent brute-force oracle."
  - "We compare a sanity greedy (C0), an exact branch-and-bound (C1), an independent exact Dijkstra-with-state reimplementation (C2 — NOT a published library; OR-Tools unavailable in this environment), and a constraint-aware A* planner with honest status reporting."
  - "On this benchmark all exact methods achieve zero false infeasibility and zero optimality gap; the sanity greedy shows {{CELL:c0_false_inf}} false infeasibilities and mean gap {{CELL:c0_gap}}; the alternative-blind mutation reproduces the legacy failure family ({{CELL:a3_false_inf}} false infeasibilities). The expected null result versus C1 is reported per the preregistered H0."

research_questions:
  rq1: >
    When multiple pedagogically equivalent activities can satisfy one goal, does
    constraint-aware selection reduce false infeasibility or cost regret under
    hard resource constraints compared with sanity and exact baselines?

formal_objective: see research_v3/methods/p02/METHOD.md section 2 (frozen)

complexity_statement: >
  NP-hard: with zero travel and empty prerequisites the objective reduces to
  minimum-weight set cover (Karp 1972). With travel, ordering the chosen
  subset embeds asymmetric TSP. No polynomial-time exact algorithm is claimed;
  exactness claims are scoped to completed searches within stated budgets.

related_work:
  - "Set cover and minimum-weight covering (Karp 1972; Chvatal 1979 greedy approximation)."
  - "Orienteering and team orienteering problems (budgeted prize-collecting routes; Vansteenwegen et al. 2011)."
  - "Constrained shortest path with resource constraints (Handler & Zang 1980; RCSP surveys)."
  - "Prerequisite-aware curriculum planning as DAG/hypergraph optimisation (classical course-timetabling and learning-path literature)."
  - "Robust/uncertainty-aware selection (chance-constrained programs; Bertsimas & Sim 2004) — motivation for uncertainty-aware alternatives in the P02 spec."
  - "CP-SAT / MILP exact reference solvers (Perron & Didier; OR-Tools) — the intended C2 published comparator; BLOCKED here (not installed), C2 delivered as an independent exact reimplementation and labelled as such."
  - "LN-06 (V2) heritage-trail planning: documented the legacy false-infeasibility bug this paper formalizes."

method_summary: see research_v3/methods/p02/METHOD.md (modules, statuses, gates)

evaluation:
  benchmark: 6 families x 3 regimes x 3 densities x 30 replications, seed 20261115
  metrics: [exact_match_rate, false_infeasibility, mean_relative_gap, wall_ms_p95]
  stats: Wilcoxon signed-rank + cluster bootstrap CI (family_id), Holm across confirmatory family
  artifacts: research_artifacts_v3/runs/p02/{instances,predictions}.jsonl + study_metric.json

results_tables:
  main_table: "Per-solver: exact_match_rate, feasibility, false infeasibility, gap, p95 runtime ({{CELL:main_table}})."
  per_regime: "Tight/mid/loose breakdown including cost_exceeded stratum ({{CELL:per_regime}})."
  per_family: "Family-level failure analysis; unreachable_bridge and blocked_access must be zero-feasibility families ({{CELL:per_family}})."

negative_results:
  - "Proposed matches C1 exactly on this benchmark scale; no quality gain is claimed (H0 not rejected)."
  - "An earlier sum-of-cheapest-providers heuristic for A* was found inadmissible via certified brute-force mismatch and replaced by a safe max-based bound (documented in METHOD.md)."
  - "Runtime: proposed p95 wall ms {{CELL:proposed_p95}} vs C1 {{CELL:c1_p95}} — any advantage is order-of-magnitude only on shared hardware."

threats_to_validity:
  - "Synthetic instances only; external validity requires the blocked dataset gate (MOOCCubeX/Junyi/CausalEdu rights cards)."
  - "Oracle envelope caps instances at 12 activities; solver behaviour beyond that is exercised only by unit tests with mutually-consistent exact solvers, not by certified ground truth."
  - "Held-Karp ordering capped at 2^18 states; larger subsets degrade to Kahn with honest status downgrade."
  - "Wall-clock timings are hardware-dependent and noisy; no statistical claims on runtime."
  - "The proposed planner and C1 share the ordering DP; ordering-stage bugs could be masked — the independent oracle (permutation/DP from first principles) is the guard."

appendices:
  - pseudocode: METHOD.md section 3 + module docstrings
  - reproducibility: "python -m research_v3.methods.p02.benchmark --instances-per-cell 30 --seed 20261115"
  - artifact_hashes: research_artifacts_v3/runs/p02/manifest.json
