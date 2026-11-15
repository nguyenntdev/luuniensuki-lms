"""Runner alias: ablation A3 — due-date scheduling disabled.

Mechanism isolated: ``due_scheduling_enabled=False``. Not-due reviews are no
longer postponed and are scheduled immediately when gates pass.
"""
from .ablations import ABLATION_FLAGS, make_predict_batch  # noqa: F401

predict_batch = make_predict_batch("ablations_a3")
