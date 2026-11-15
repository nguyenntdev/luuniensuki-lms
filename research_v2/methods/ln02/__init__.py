"""LN-02 method package: proposed policy, baselines, ablations, adapters.

Runner-facing method ids (``research_v2.methods.ln02.<method_id>``):
- ``proposed``            - non-compensatory prerequisite-aware policy (I1)
- ``baselines_b0``        - naive aggregate-score recommender (C0, sanity)
- ``baselines_c1``        - Rasch 1-PL scalar ability, no prerequisite DAG (C1)
- ``ablations_a1..a3``    - mechanism-isolating ablations
- ``legacy_adapter``      - read-only bridge to the audited legacy engine
"""
from . import (
    ablations,
    baselines,
    core,
    legacy_adapter,
    metrics,
    proposed,
)

__all__ = [
    "ablations",
    "baselines",
    "core",
    "legacy_adapter",
    "metrics",
    "proposed",
]
