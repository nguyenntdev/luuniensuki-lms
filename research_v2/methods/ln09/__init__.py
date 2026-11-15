"""LN-09 — Source-Auditable Teacher Decision Support under Incomplete Learning Analytics.

Research V2 method package. All policies are pure decision functions over
``StudyInput`` features (time-ordered learner signals, source/task provenance,
teacher capacity budget) with no oracle access.

Label-space divergence (documented, not silently absorbed):
    The frozen T3 gold for LN-09 (``research_v2/data/ln09/t3_gold.jsonl``) is
    materialized in the legacy engine vocabulary
    (``backend.domain.instructional_recommendations.DecisionCode``:
    ``propose_explained_action / abstain_missing_evidence / abstain_conflict /
    abstain_unverified_source / request_refresh``). The shared contract label
    space ``research_v2.contracts.label_space.LN09_DECISIONS`` uses the
    V2 abstraction framing (``recommend_action / descriptive_only /
    abstain_insufficient_data / require_teacher_override``). Predictions are
    emitted in the gold-compatible legacy vocabulary so the sealed evaluator
    scores them verbatim; the deterministic gold->V2 mapping lives in
    ``metrics.py`` (evaluator-side only).
"""
