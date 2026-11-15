"""LN-07 — Cognitive-Equivalent Multimodal Heritage Learning under Resource Constraints.

Method package for the Research V2 study LN-07. The proposed policy is a UDL
affordance-preservation engine: a modality choice is pedagogically equivalent
only when it preserves every required affordance (image, inscription text,
transcript, audio description, keyboard operability, screen-reader semantics).
A 2D raster fallback that has an image but omits the inscription the task
requires is NOT equivalent — the engine flags the missing affordance and
routes to a sufficient modality or rejects.
"""
from research_v2.methods.ln07.labels import DECISION_LABELS, Decision, LabelError

__all__ = ["DECISION_LABELS", "Decision", "LabelError"]
