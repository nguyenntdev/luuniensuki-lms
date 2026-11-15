"""Runner alias: B0 always-schedule sanity baseline for the LN-03 matrix.

Compositor status: REIMPLEMENTATION (negative control, SANITY_ONLY).
Imports the independent B0 policy; never reuses the proposed decision path.
"""
from .baselines import (  # noqa: F401
    COMPARATOR_STATUS,
    b0_decide,
    predict_batch_b0 as predict_batch,
)
