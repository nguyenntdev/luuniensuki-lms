"""P07 Baselines:
C0: URL-Present Sanity Baseline.
C1: Static Image Fallback Baseline (ignores inscription affordance).
C2 / B*: SigLIP2 Multimodal Greedy Reranker (ranks purely by semantic relevance without rights or device closure).
"""
from __future__ import annotations

from typing import Optional, Sequence
from .method import (
    ALLOWED_LICENSES,
    BANDWIDTH_CEILING_KBPS,
    DeviceProfile,
    LearningObject,
    SelectionDecision,
    TaskSpec,
)


class C0UrlPresent:
    """C0 Sanity: Returns the first candidate object with an ID, blind to rights and affordances."""
    def select(
        self,
        task: TaskSpec,
        device: DeviceProfile,
        candidates: Sequence[LearningObject],
    ) -> SelectionDecision:
        if not candidates:
            return SelectionDecision(
                status="abstain_no_candidates",
                selected_object_id=None,
                missing_affordances=(),
                reasons=("no_candidates_provided",),
                utility=0.0,
                kb_used=0,
            )
        pick = candidates[0]
        # Evaluated utility is 0 if illegal or infeasible
        is_legal = pick.license_status in ALLOWED_LICENSES and pick.provenance_verified
        is_feasible = pick.kb <= device.max_payload_kb and (pick.modality != "3d" or device.webgl)
        affords_all = all(pick.affords(r) for r in task.required_affordances)
        utility = pick.semantic_relevance if (is_legal and is_feasible and affords_all) else 0.0

        return SelectionDecision(
            status="selected",
            selected_object_id=pick.object_id,
            missing_affordances=(),
            reasons=("c0_first_url_present",),
            utility=utility,
            kb_used=pick.kb,
            license_status=pick.license_status,
        )


class C1StaticFallback:
    """C1 Classical: Prefers 3D, falls back to 2D image/rubbing, drops inscription requirement."""
    def select(
        self,
        task: TaskSpec,
        device: DeviceProfile,
        candidates: Sequence[LearningObject],
    ) -> SelectionDecision:
        if not candidates:
            return SelectionDecision(
                status="abstain_no_candidates",
                selected_object_id=None,
                missing_affordances=(),
                reasons=("no_candidates_provided",),
                utility=0.0,
                kb_used=0,
            )

        # Inscription requirement dropped in C1 check
        sub_affordances = tuple(r for r in task.required_affordances if r != "inscription_text")

        # Try 3D first
        for o in candidates:
            if o.modality == "3d" and device.webgl and o.kb <= device.max_payload_kb:
                if all(o.affords(r) for r in sub_affordances):
                    is_legal = o.license_status in ALLOWED_LICENSES and o.provenance_verified
                    affords_full = all(o.affords(r) for r in task.required_affordances)
                    util = o.semantic_relevance if (is_legal and affords_full) else 0.0
                    return SelectionDecision(
                        status="selected",
                        selected_object_id=o.object_id,
                        missing_affordances=(),
                        reasons=("c1_3d_selected",),
                        utility=util,
                        kb_used=o.kb,
                        license_status=o.license_status,
                    )

        # Fall back to first 2D image / rubbing
        for o in candidates:
            if o.modality in {"2d_image", "2d_rubbing"} and o.kb <= device.max_payload_kb:
                is_legal = o.license_status in ALLOWED_LICENSES and o.provenance_verified
                affords_full = all(o.affords(r) for r in task.required_affordances)
                util = o.semantic_relevance if (is_legal and affords_full) else 0.0
                return SelectionDecision(
                    status="selected",
                    selected_object_id=o.object_id,
                    missing_affordances=(),
                    reasons=("c1_static_fallback_dropped_inscription",),
                    utility=util,
                    kb_used=o.kb,
                    license_status=o.license_status,
                )

        return SelectionDecision(
            status="reject_device_infeasible",
            selected_object_id=None,
            missing_affordances=(),
            reasons=("c1_no_feasible_object",),
            utility=0.0,
            kb_used=0,
        )


class C2SigLIP2GreedyReranker:
    """C2 / Baseline Champion B*: SigLIP2 Multimodal Greedy Reranker.
    
    Ranks purely by highest multimodal semantic relevance score without rights certificate
    or device feasibility verification.
    """
    def select(
        self,
        task: TaskSpec,
        device: DeviceProfile,
        candidates: Sequence[LearningObject],
    ) -> SelectionDecision:
        if not candidates:
            return SelectionDecision(
                status="abstain_no_candidates",
                selected_object_id=None,
                missing_affordances=(),
                reasons=("no_candidates_provided",),
                utility=0.0,
                kb_used=0,
            )

        # Pick highest semantic relevance
        sorted_candidates = sorted(candidates, key=lambda o: (o.semantic_relevance, -o.kb), reverse=True)
        top = sorted_candidates[0]

        is_legal = top.license_status in ALLOWED_LICENSES and top.provenance_verified
        is_device_ok = (
            top.kb <= device.max_payload_kb
            and device.network_kbps >= BANDWIDTH_CEILING_KBPS.get(top.modality, 100)
            and (top.modality != "3d" or device.webgl)
            and (not device.keyboard_only or top.affords("keyboard_accessible"))
            and (not device.screen_reader or top.affords("screen_reader_ready"))
        )
        affords_all = all(top.affords(r) for r in task.required_affordances)

        # Ground-truth evaluation utility: 0 if rights violated, device broken, or missing affordance
        valid = is_legal and is_device_ok and affords_all
        utility = top.semantic_relevance if valid else 0.0

        return SelectionDecision(
            status="selected",
            selected_object_id=top.object_id,
            missing_affordances=(),
            reasons=("c2_siglip2_greedy_top_relevance",),
            utility=utility,
            kb_used=top.kb,
            license_status=top.license_status,
        )
