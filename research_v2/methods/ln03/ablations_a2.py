"""Runner alias: ablation A2 — fact-stability gate disabled.

Mechanism isolated: ``fact_stability_enabled=False``. Generative explanation is
assigned before any stable fact recall (the mandatory LN-03 counterexample).
"""
from .ablations import ABLATION_FLAGS, make_predict_batch  # noqa: F401

predict_batch = make_predict_batch("ablations_a2")
