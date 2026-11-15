"""LN-06 — Constrained Heritage Trail Planning with Alternative Learning Stops.

Method package for the Research V2 study LN-06. The proposed policy performs
minimum-cost feasible stop-subset selection covering target outcomes plus the
transitive prerequisite closure, then emits a topological visit order with
deterministic tie-breaking; travel edges are honoured when present.
"""
from research_v2.methods.ln06.labels import DECISION_VALUES, Decision, LabelError

__all__ = ["DECISION_VALUES", "Decision", "LabelError"]
