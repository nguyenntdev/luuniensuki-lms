# /goal — LƯU NIÊN research V3 / execute-to-evidence

You are the coordinator of **10 concurrent subagents** working on repo `https://github.com/nguyenntdev/luuniensuki-lms`. READ all files in this package first and inspect current GitHub HEAD. Snapshot baseline expected at creation: `6debec211f240375f5b967fe2eac7f6450c3e53c`; if HEAD moved, compare and create an audit delta before proceeding. The prior `research/`, `research_v2/`, `manuscripts_v5/` and `research_artifacts*` are historical and must remain reproducible and unmodified unless a narrowly reviewed bugfix is necessary.

**Goal:** implement every code-implementable TODO in `06_TASK_TRACKER/V3_TASK_REGISTER.csv`, across the 14 V3 P01–P14 papers, until there are no unresolved code/software experiment tasks. For all blocked human actions (licensing, consent, expert annotations, empirical evaluation, writing approval), prepare the exact forms/artifacts and leave them honestly BLOCKED. NEVER falsely claim all papers are completed because a license/IRB/human participant is missing. Conditional P04/P08 must be merged or stopped if independence fails.

## Nonnegotiable execution loop
1. Parse the task CSV, build DAG, choose ready tasks and assign 10 distinct file ownership lanes from `07_AGENTS/10_AGENT_EXECUTION_PLAN.md`.
2. For each ticket: inspect current source, cite path/line, implement smallest correct addition, add positive/negative and failure-mode tests, run tests, record evidence path, SHA, rerun command, then update task status with reviewer approval.
3. Fail-closed source data: verify official external datasets and terms; never download restricted files into Git; no unauthorized student PII. Use only public research-approved sources.
4. Build serious matched baselines and tests before proposed performance claims. Never use frozen holdout for tuning, nor generate fake expert labels, fake learning gains, fake baseline metrics or synthetic real-world evidence.
5. Serialize all peer-reviewed outputs: dataset cards, model cards, run manifests, frozen split hashes, paired statistics, ablation tables, failures, cost, calibration and citation ledger.
6. When a result does not beat a baseline, report it as null/negative and proceed to objective scientific review — never tweak frozen labels or alter evaluation until it passes.
7. Require independent review for each primary result; no paper may share a duplicated primary hypothesis/primary outcome without explicit merge decision.
8. Every 10 tasks, write machine-readable `research_artifacts_v3/release/progress.json` with done/blocked/fail counts, SHA, links and exact next-ready tasks.
9. Use the existing tests and CI as regression gates. No main branch force pushes, no deployments, email, real participant recruitment or institution approvals without explicit authorization.
10. Stop only when all implementable tasks are DONE/validated and all remaining external prerequisites are individually BLOCKED with evidence and human owner. Do not claim future background work is completed.

## Delivery contract
- 14 paper packets present and frozen; each has dataset provenance, closest literature, RQ, method and comparators, tests, signed analysis (when obtainable), manuscript and release manifest.
- Research V3 code/config/tests in isolated directories, reproducible clean-environment commands, cross-study integrity checks, no fabricated results.
- Report exact statuses (engineering vs scientific vs submission) and obtain human approvals only through real records.

Start at W0. Do not skip source audit or claim that `LN-xx` results prove new `Pxx` paper quality.
