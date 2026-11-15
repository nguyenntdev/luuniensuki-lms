"""Runner alias: ablation A1 — verified-source gate disabled.

Mechanism isolated: ``source_gate_enabled=False``. Unverified sources no longer
block generative explanation assignments.
"""
from .ablations import ABLATION_FLAGS, make_predict_batch  # noqa: F401

predict_batch = make_predict_batch("ablations_a1")
