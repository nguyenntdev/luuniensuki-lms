"""P07 Proposed Winning Method:
Rights-Aware Affordance-Complete Constrained ILP Selector (RAC-ILP).

Addresses V3 failure (8 cases, unverified licenses, ungrounded fallbacks, Holm p=0.75):
Mechanism:
1. Provenance and Rights Certificate Closure: Discards candidates with invalid,
   unverified, or restrictive licenses (only CC0, CC-BY, CC-BY-SA, Open Heritage).
2. Device & Accessibility Feasibility Check: Strictly enforces payload budget B,
   network streaming ceiling, WebGL requirement for 3D meshes, and screen-reader/keyboard
   accessibility flags.
3. Affordance-Completeness Verification: Enforces o.affords(r) == True for all r in R(T).
   If none cover, cleanly emits typed failure 'abstain_missing_affordance' rather than
   silent degraded substitution.
4. Exact Constrained Optimization (ILP / Multi-criteria Knapsack):
   Among feasible candidates, maximizes utility:
     U(o) = relevance(o) - lambda_cost * (kb(o) / max_payload) + mu_prov * provenance_score(o)
   with deterministic tie-breaking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple
import hashlib
import json

ALLOWED_LICENSES = frozenset({
    "CC0", "CC0-1.0", "CC-BY", "CC-BY-4.0", "CC-BY-SA", "CC-BY-SA-4.0", "OpenHeritage-1.0"
})

BANDWIDTH_CEILING_KBPS = {
    "3d": 500,
    "2d_image": 100,
    "2d_rubbing": 80,
    "audio": 64,
    "text": 10,
}


@dataclass(frozen=True)
class LearningObject:
    object_id: str
    modality: str  # '3d', '2d_image', '2d_rubbing', 'audio', 'text'
    license_status: str
    kb: int
    affordances: Dict[str, bool]
    semantic_relevance: float
    provenance_verified: bool = True
    source_provider: str = "chau_ban_trieu_nguyen"

    def affords(self, key: str) -> bool:
        return self.affordances.get(key) is True


@dataclass(frozen=True)
class DeviceProfile:
    max_payload_kb: int
    network_kbps: int
    webgl: bool = True
    keyboard_only: bool = False
    screen_reader: bool = False


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    required_affordances: Tuple[str, ...]
    min_relevance: float = 0.20


@dataclass(frozen=True)
class SelectionDecision:
    status: str  # 'selected', 'reject_rights_violation', 'reject_device_infeasible', 'abstain_missing_affordance', 'abstain_no_candidates'
    selected_object_id: Optional[str]
    missing_affordances: Tuple[str, ...]
    reasons: Tuple[str, ...]
    utility: float
    kb_used: int = 0
    license_status: Optional[str] = None


class RightsAwareILPSelector:
    """Proposed Winning Method: Rights-Aware Affordance-Complete Selector."""
    def __init__(self, lambda_cost: float = 0.15, mu_prov: float = 0.10):
        self.lambda_cost = lambda_cost
        self.mu_prov = mu_prov

    def check_rights(self, obj: LearningObject) -> bool:
        if not obj.provenance_verified:
            return False
        return obj.license_status in ALLOWED_LICENSES

    def check_device(self, obj: LearningObject, device: DeviceProfile) -> Tuple[bool, List[str]]:
        reasons = []
        if obj.kb > device.max_payload_kb:
            reasons.append("payload_exceeded")
        ceiling = BANDWIDTH_CEILING_KBPS.get(obj.modality, 100)
        if device.network_kbps < ceiling:
            reasons.append("network_bandwidth_insufficient")
        if obj.modality == "3d" and not device.webgl:
            reasons.append("webgl_unsupported")
        if device.keyboard_only and not obj.affords("keyboard_accessible"):
            reasons.append("keyboard_inaccessible")
        if device.screen_reader and not obj.affords("screen_reader_ready"):
            reasons.append("screen_reader_inaccessible")
        return len(reasons) == 0, reasons

    def check_affordances(self, obj: LearningObject, task: TaskSpec) -> Tuple[bool, Tuple[str, ...]]:
        missing = tuple(r for r in task.required_affordances if not obj.affords(r))
        return len(missing) == 0, missing

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

        # 1. Screen rights
        rights_cleared = [o for o in candidates if self.check_rights(o)]
        if not rights_cleared:
            return SelectionDecision(
                status="reject_rights_violation",
                selected_object_id=None,
                missing_affordances=(),
                reasons=("all_candidates_fail_license_or_provenance",),
                utility=0.0,
                kb_used=0,
            )

        # 2. Screen device feasibility
        device_feasible = []
        for o in rights_cleared:
            ok, _ = self.check_device(o, device)
            if ok:
                device_feasible.append(o)

        if not device_feasible:
            return SelectionDecision(
                status="reject_device_infeasible",
                selected_object_id=None,
                missing_affordances=(),
                reasons=("no_candidate_satisfies_device_constraints",),
                utility=0.0,
                kb_used=0,
            )

        # 3. Screen affordances
        covering = []
        min_missing: Tuple[str, ...] = task.required_affordances
        for o in device_feasible:
            ok, missing = self.check_affordances(o, task)
            if ok:
                covering.append(o)
            elif len(missing) < len(min_missing):
                min_missing = missing

        if not covering:
            return SelectionDecision(
                status="abstain_missing_affordance",
                selected_object_id=None,
                missing_affordances=min_missing,
                reasons=("candidate_objects_lack_required_affordances",),
                utility=0.0,
                kb_used=0,
            )

        # 4. Multi-criteria optimization among covering & feasible objects
        best_obj: Optional[LearningObject] = None
        best_utility = -1e9

        for o in covering:
            cost_norm = o.kb / max(device.max_payload_kb, 1)
            prov_bonus = self.mu_prov if o.provenance_verified else 0.0
            utility = o.semantic_relevance - (self.lambda_cost * cost_norm) + prov_bonus
            # Deterministic tie break on utility, then lowest kb, then object_id
            if utility > best_utility:
                best_utility = utility
                best_obj = o
            elif abs(utility - best_utility) < 1e-9:
                if best_obj is not None and o.kb < best_obj.kb:
                    best_obj = o
                elif best_obj is not None and o.kb == best_obj.kb and o.object_id < best_obj.object_id:
                    best_obj = o

        assert best_obj is not None
        return SelectionDecision(
            status="selected",
            selected_object_id=best_obj.object_id,
            missing_affordances=(),
            reasons=("affordance_complete_rights_feasible",),
            utility=max(0.0, best_utility),
            kb_used=best_obj.kb,
            license_status=best_obj.license_status,
        )
