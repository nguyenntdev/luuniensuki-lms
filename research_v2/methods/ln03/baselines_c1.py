"""Runner alias: C1 strong classical Leitner 5-box baseline for the LN-03 matrix.

Compositor status: REIMPLEMENTATION (classical Leitner box scheduler).
Enforces the fact prerequisite but deliberately omits the source gate —
the documented failure mode of classical schedulers on grounded tasks.
"""
from .baselines import (  # noqa: F401
    COMPARATOR_STATUS,
    LEITNER_BOXES,
    LEITNER_DEFAULT_GRADATIONS,
    c1_decide,
    predict_batch_c1 as predict_batch,
)
